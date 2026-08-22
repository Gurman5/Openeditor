"""Australian English spelling corrections applied as Word tracked changes.

Scans every body-text run in the document for American English spellings and
replaces them with Australian equivalents using <w:del> / <w:ins> pairs so the
editor can accept or reject each change individually in Microsoft Word.
"""

import os
import re
import zipfile
from copy import deepcopy

from lxml import etree

from app.services.document_zones import (
    SKIP_STYLES as _SHARED_SKIP_STYLES,
)
from app.services.document_zones import (
    iter_paragraphs_with_zone,
    should_skip_paragraph,
)
from app.services.output_generation import (
    _make_comment_element,
    _patch_content_types,
    _patch_rels,
)
from app.services.quotation_utils import find_quote_spans
from app.services.timestamps import now_sydney_iso

W = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"
WQ = f"{{{W}}}"
AUTHOR = "CopyEditor AI"
DATE = now_sydney_iso()

# Paragraph styles that should NOT be spell-corrected. Re-exported from
# :mod:`app.services.document_zones` so every prose-mutating correction pass
# agrees on the skip set — headings, reference list, front-matter labels,
# captions. See document_zones.SKIP_STYLES for the canonical source.
# (Merge note: develop added the "APA7ReferenceListEntry" alias inline; that
# alias is now part of document_zones.SKIP_STYLES so this re-export still
# covers every paragraph style the inline version did.)
_SKIP_STYLES = _SHARED_SKIP_STYLES


def summarize_spelling_correction_repeats(corrections: list[dict]) -> list[dict]:
    """Return one summary entry per repeated spelling correction.

    The tracked-change pass still fixes every occurrence in the document. This
    helper only reduces the result-panel summary so repeated spelling changes
    are shown once with a count of later repeats grouped under that first item.
    """
    grouped: dict[tuple[str, str], dict] = {}
    for correction in corrections:
        original = str(correction.get("original", ""))
        replacement = str(correction.get("replacement", ""))
        key = (original.casefold(), replacement.casefold())
        if key not in grouped:
            grouped[key] = {**correction, "grouped_repeats": 0}
            continue
        grouped[key]["grouped_repeats"] += 1
    return list(grouped.values())


def _comment_range_start(comment_id: int) -> etree._Element:
    start = etree.Element(f"{WQ}commentRangeStart", nsmap={"w": W})
    start.set(f"{WQ}id", str(comment_id))
    return start


def _comment_range_end(comment_id: int) -> etree._Element:
    end = etree.Element(f"{WQ}commentRangeEnd", nsmap={"w": W})
    end.set(f"{WQ}id", str(comment_id))
    return end


def _comment_reference_run(comment_id: int) -> etree._Element:
    ref_run = etree.Element(f"{WQ}r", nsmap={"w": W})
    r_pr = etree.SubElement(ref_run, f"{WQ}rPr")
    r_style = etree.SubElement(r_pr, f"{WQ}rStyle")
    r_style.set(f"{WQ}val", "CommentReference")
    comment_ref = etree.SubElement(ref_run, f"{WQ}commentReference")
    comment_ref.set(f"{WQ}id", str(comment_id))
    return ref_run


def _spelling_comment_text(original: str, replacement: str, count: int) -> str:
    later = max(count - 1, 0)
    repeat_text = (
        f"{later} later occurrence{'s' if later != 1 else ''} of the same spelling issue "
        f"{'was' if later == 1 else 'were'} fixed with tracked changes only."
        if later
        else "No later repeats of this spelling issue were found."
    )
    return (
        f'US spelling "{original}" was changed to Australian English '
        f'"{replacement}". {repeat_text}'
    )


def _spelling_summary_comment_text(comment_summaries: list[dict]) -> str:
    """Build one Word comment for all AU spelling replacements."""
    if len(comment_summaries) == 1:
        summary = comment_summaries[0]
        return _spelling_comment_text(
            summary["original"],
            summary["replacement"],
            summary["count"],
        )

    pairs = []
    total = 0
    for summary in comment_summaries:
        count = int(summary.get("count", 0))
        total += count
        label = "occurrence" if count == 1 else "occurrences"
        pairs.append(
            f'{summary["original"]} \u2192 {summary["replacement"]} '
            f"({count} {label})"
        )
    pair_text = "; ".join(pairs)
    return (
        f"{total} US spellings were changed to Australian English with tracked "
        f"changes: {pair_text}."
    )

# ---------------------------------------------------------------------------
# American → Australian English dictionary
# Only unambiguous, common differences relevant to academic writing.
# Keys must be lowercase.
# ---------------------------------------------------------------------------
AU_CORRECTIONS: dict[str, str] = {

    # -------------------------------------------------------------------------
    # -ize → -ise  (base + inflections: -izes/-ised/-izing for every verb)
    # -------------------------------------------------------------------------
    "actualize": "actualise",
    "actualizes": "actualises",
    "actualized": "actualised",
    "actualizing": "actualising",
    "analyze": "analyse",
    "analyzes": "analyses",
    "analyzed": "analysed",
    "analyzing": "analysing",
    "apologize": "apologise",
    "apologizes": "apologises",
    "apologized": "apologised",
    "apologizing": "apologising",
    "authorize": "authorise",
    "authorizes": "authorises",
    "authorized": "authorised",
    "authorizing": "authorising",
    "brutalize": "brutalise",
    "brutalizes": "brutalises",
    "brutalized": "brutalised",
    "brutalizing": "brutalising",
    "capitalize": "capitalise",
    "capitalizes": "capitalises",
    "capitalized": "capitalised",
    "capitalizing": "capitalising",
    "categorize": "categorise",
    "categorizes": "categorises",
    "categorized": "categorised",
    "categorizing": "categorising",
    "centralize": "centralise",
    "centralizes": "centralises",
    "centralized": "centralised",
    "centralizing": "centralising",
    "characterize": "characterise",
    "characterizes": "characterises",
    "characterized": "characterised",
    "characterizing": "characterising",
    "civilize": "civilise",
    "civilizes": "civilises",
    "civilized": "civilised",
    "civilizing": "civilising",
    "colonize": "colonise",
    "colonizes": "colonises",
    "colonized": "colonised",
    "colonizing": "colonising",
    "commercialize": "commercialise",
    "commercializes": "commercialises",
    "commercialized": "commercialised",
    "commercializing": "commercialising",
    "conceptualize": "conceptualise",
    "conceptualizes": "conceptualises",
    "conceptualized": "conceptualised",
    "conceptualizing": "conceptualising",
    "contextualize": "contextualise",
    "contextualizes": "contextualises",
    "contextualized": "contextualised",
    "contextualizing": "contextualising",
    "criticize": "criticise",
    "criticizes": "criticises",
    "criticized": "criticised",
    "criticizing": "criticising",
    "crystallize": "crystallise",
    "crystallizes": "crystallises",
    "crystallized": "crystallised",
    "crystallizing": "crystallising",
    "customize": "customise",
    "customizes": "customises",
    "customized": "customised",
    "customizing": "customising",
    "decolonize": "decolonise",
    "decolonizes": "decolonises",
    "decolonized": "decolonised",
    "decolonizing": "decolonising",
    "democratize": "democratise",
    "democratizes": "democratises",
    "democratized": "democratised",
    "democratizing": "democratising",
    "destigmatize": "destigmatise",
    "destigmatizes": "destigmatises",
    "destigmatized": "destigmatised",
    "destigmatizing": "destigmatising",
    "digitize": "digitise",
    "digitizes": "digitises",
    "digitized": "digitised",
    "digitizing": "digitising",
    "dramatize": "dramatise",
    "dramatizes": "dramatises",
    "dramatized": "dramatised",
    "dramatizing": "dramatising",
    "emphasize": "emphasise",
    "emphasizes": "emphasises",
    "emphasized": "emphasised",
    "emphasizing": "emphasising",
    "equalize": "equalise",
    "equalizes": "equalises",
    "equalized": "equalised",
    "equalizing": "equalising",
    "familiarize": "familiarise",
    "familiarizes": "familiarises",
    "familiarized": "familiarised",
    "familiarizing": "familiarising",
    "fantasize": "fantasise",
    "fantasizes": "fantasises",
    "fantasized": "fantasised",
    "fantasizing": "fantasising",
    "fertilize": "fertilise",
    "fertilizes": "fertilises",
    "fertilized": "fertilised",
    "fertilizing": "fertilising",
    "finalize": "finalise",
    "finalizes": "finalises",
    "finalized": "finalised",
    "finalizing": "finalising",
    "formalize": "formalise",
    "formalizes": "formalises",
    "formalized": "formalised",
    "formalizing": "formalising",
    "fossilize": "fossilise",
    "fossilizes": "fossilises",
    "fossilized": "fossilised",
    "fossilizing": "fossilising",
    "galvanize": "galvanise",
    "galvanizes": "galvanises",
    "galvanized": "galvanised",
    "galvanizing": "galvanising",
    "generalizable": "generalisable",
    "generalize": "generalise",
    "generalizes": "generalises",
    "generalized": "generalised",
    "generalizing": "generalising",
    "globalize": "globalise",
    "globalizes": "globalises",
    "globalized": "globalised",
    "globalizing": "globalising",
    "harmonize": "harmonise",
    "harmonizes": "harmonises",
    "harmonized": "harmonised",
    "harmonizing": "harmonising",
    "homogenize": "homogenise",
    "homogenizes": "homogenises",
    "homogenized": "homogenised",
    "homogenizing": "homogenising",
    "hypothesize": "hypothesise",
    "hypothesizes": "hypothesises",
    "hypothesized": "hypothesised",
    "hypothesizing": "hypothesising",
    "idealize": "idealise",
    "idealizes": "idealises",
    "idealized": "idealised",
    "idealizing": "idealising",
    "immunize": "immunise",
    "immunizes": "immunises",
    "immunized": "immunised",
    "immunizing": "immunising",
    "incentivize": "incentivise",
    "incentivizes": "incentivises",
    "incentivized": "incentivised",
    "incentivizing": "incentivising",
    "individualize": "individualise",
    "individualizes": "individualises",
    "individualized": "individualised",
    "individualizing": "individualising",
    "industrialize": "industrialise",
    "industrializes": "industrialises",
    "industrialized": "industrialised",
    "industrializing": "industrialising",
    "initialize": "initialise",
    "initializes": "initialises",
    "initialized": "initialised",
    "initializing": "initialising",
    "institutionalize": "institutionalise",
    "institutionalizes": "institutionalises",
    "institutionalized": "institutionalised",
    "institutionalizing": "institutionalising",
    "internalize": "internalise",
    "internalizes": "internalises",
    "internalized": "internalised",
    "internalizing": "internalising",
    "jeopardize": "jeopardise",
    "jeopardizes": "jeopardises",
    "jeopardized": "jeopardised",
    "jeopardizing": "jeopardising",
    "legalize": "legalise",
    "legalizes": "legalises",
    "legalized": "legalised",
    "legalizing": "legalising",
    "legitimize": "legitimise",
    "legitimizes": "legitimises",
    "legitimized": "legitimised",
    "legitimizing": "legitimising",
    "localize": "localise",
    "localizes": "localises",
    "localized": "localised",
    "localizing": "localising",
    "marginalize": "marginalise",
    "marginalizes": "marginalises",
    "marginalized": "marginalised",
    "marginalizing": "marginalising",
    "maximize": "maximise",
    "maximizes": "maximises",
    "maximized": "maximised",
    "maximizing": "maximising",
    "mechanize": "mechanise",
    "mechanizes": "mechanises",
    "mechanized": "mechanised",
    "mechanizing": "mechanising",
    "medicalize": "medicalise",
    "medicalizes": "medicalises",
    "medicalized": "medicalised",
    "medicalizing": "medicalising",
    "memorize": "memorise",
    "memorizes": "memorises",
    "memorized": "memorised",
    "memorizing": "memorising",
    "minimize": "minimise",
    "minimizes": "minimises",
    "minimized": "minimised",
    "minimizing": "minimising",
    "mobilize": "mobilise",
    "mobilizes": "mobilises",
    "mobilized": "mobilised",
    "mobilizing": "mobilising",
    "modernize": "modernise",
    "modernizes": "modernises",
    "modernized": "modernised",
    "modernizing": "modernising",
    "nationalize": "nationalise",
    "nationalizes": "nationalises",
    "nationalized": "nationalised",
    "nationalizing": "nationalising",
    "naturalize": "naturalise",
    "naturalizes": "naturalises",
    "naturalized": "naturalised",
    "naturalizing": "naturalising",
    "neutralize": "neutralise",
    "neutralizes": "neutralises",
    "neutralized": "neutralised",
    "neutralizing": "neutralising",
    "normalize": "normalise",
    "normalizes": "normalises",
    "normalized": "normalised",
    "normalizing": "normalising",
    "operationalize": "operationalise",
    "operationalizes": "operationalises",
    "operationalized": "operationalised",
    "operationalizing": "operationalising",
    "optimize": "optimise",
    "optimizes": "optimises",
    "optimized": "optimised",
    "optimizing": "optimising",
    "organize": "organise",
    "organizes": "organises",
    "organized": "organised",
    "organizing": "organising",
    "penalize": "penalise",
    "penalizes": "penalises",
    "penalized": "penalised",
    "penalizing": "penalising",
    "personalize": "personalise",
    "personalizes": "personalises",
    "personalized": "personalised",
    "personalizing": "personalising",
    "polarize": "polarise",
    "polarizes": "polarises",
    "polarized": "polarised",
    "polarizing": "polarising",
    "popularize": "popularise",
    "popularizes": "popularises",
    "popularized": "popularised",
    "popularizing": "popularising",
    "prioritize": "prioritise",
    "prioritizes": "prioritises",
    "prioritized": "prioritised",
    "prioritizing": "prioritising",
    "privatize": "privatise",
    "privatizes": "privatises",
    "privatized": "privatised",
    "privatizing": "privatising",
    "problematize": "problematise",
    "problematizes": "problematises",
    "problematized": "problematised",
    "problematizing": "problematising",
    "professionalize": "professionalise",
    "professionalizes": "professionalises",
    "professionalized": "professionalised",
    "professionalizing": "professionalising",
    "publicize": "publicise",
    "publicizes": "publicises",
    "publicized": "publicised",
    "publicizing": "publicising",
    "radicalize": "radicalise",
    "radicalizes": "radicalises",
    "radicalized": "radicalised",
    "radicalizing": "radicalising",
    "rationalize": "rationalise",
    "rationalizes": "rationalises",
    "rationalized": "rationalised",
    "rationalizing": "rationalising",
    "realize": "realise",
    "realizes": "realises",
    "realized": "realised",
    "realizing": "realising",
    "recognize": "recognise",
    "recognizes": "recognises",
    "recognized": "recognised",
    "recognizing": "recognising",
    "regularize": "regularise",
    "regularizes": "regularises",
    "regularized": "regularised",
    "regularizing": "regularising",
    "reorganize": "reorganise",
    "reorganizes": "reorganises",
    "reorganized": "reorganised",
    "reorganizing": "reorganising",
    "revolutionize": "revolutionise",
    "revolutionizes": "revolutionises",
    "revolutionized": "revolutionised",
    "revolutionizing": "revolutionising",
    "sanitize": "sanitise",
    "sanitizes": "sanitises",
    "sanitized": "sanitised",
    "sanitizing": "sanitising",
    "serialize": "serialise",
    "serializes": "serialises",
    "serialized": "serialised",
    "serializing": "serialising",
    "socialize": "socialise",
    "socializes": "socialises",
    "socialized": "socialised",
    "socializing": "socialising",
    "specialize": "specialise",
    "specializes": "specialises",
    "specialized": "specialised",
    "specializing": "specialising",
    "stabilize": "stabilise",
    "stabilizes": "stabilises",
    "stabilized": "stabilised",
    "stabilizing": "stabilising",
    "standardize": "standardise",
    "standardizes": "standardises",
    "standardized": "standardised",
    "standardizing": "standardising",
    "sterilize": "sterilise",
    "sterilizes": "sterilises",
    "sterilized": "sterilised",
    "sterilizing": "sterilising",
    "stigmatize": "stigmatise",
    "stigmatizes": "stigmatises",
    "stigmatized": "stigmatised",
    "stigmatizing": "stigmatising",
    "subsidize": "subsidise",
    "subsidizes": "subsidises",
    "subsidized": "subsidised",
    "subsidizing": "subsidising",
    "summarize": "summarise",
    "summarizes": "summarises",
    "summarized": "summarised",
    "summarizing": "summarising",
    "sympathize": "sympathise",
    "sympathizes": "sympathises",
    "sympathized": "sympathised",
    "sympathizing": "sympathising",
    "symbolize": "symbolise",
    "symbolizes": "symbolises",
    "symbolized": "symbolised",
    "symbolizing": "symbolising",
    "synthesize": "synthesise",
    "synthesizes": "synthesises",
    "synthesized": "synthesised",
    "synthesizing": "synthesising",
    "systematize": "systematise",
    "systematizes": "systematises",
    "systematized": "systematised",
    "systematizing": "systematising",
    "terrorize": "terrorise",
    "terrorizes": "terrorises",
    "terrorized": "terrorised",
    "terrorizing": "terrorising",
    "theorize": "theorise",
    "theorizes": "theorises",
    "theorized": "theorised",
    "theorizing": "theorising",
    "trivialize": "trivialise",
    "trivializes": "trivialises",
    "trivialized": "trivialised",
    "trivializing": "trivialising",
    "urbanize": "urbanise",
    "urbanizes": "urbanises",
    "urbanized": "urbanised",
    "urbanizing": "urbanising",
    "utilize": "utilise",
    "utilizes": "utilises",
    "utilized": "utilised",
    "utilizing": "utilising",
    "vaporize": "vaporise",
    "vaporizes": "vaporises",
    "vaporized": "vaporised",
    "vaporizing": "vaporising",
    "visualize": "visualise",
    "visualizes": "visualises",
    "visualized": "visualised",
    "visualizing": "visualising",
    "vocalize": "vocalise",
    "vocalizes": "vocalises",
    "vocalized": "vocalised",
    "vocalizing": "vocalising",
    "weaponize": "weaponise",
    "weaponizes": "weaponises",
    "weaponized": "weaponised",
    "weaponizing": "weaponising",
    "computerize": "computerise",
    "computerizes": "computerises",
    "computerized": "computerised",
    "computerizing": "computerising",
    "demonize": "demonise",
    "demonizes": "demonises",
    "demonized": "demonised",
    "demonizing": "demonising",
    "energize": "energise",
    "energizes": "energises",
    "energized": "energised",
    "energizing": "energising",
    "ostracize": "ostracise",
    "ostracizes": "ostracises",
    "ostracized": "ostracised",
    "ostracizing": "ostracising",
    "paralyze": "paralyse",
    "paralyzes": "paralyses",
    "paralyzed": "paralysed",
    "paralyzing": "paralysing",
    "patronize": "patronise",
    "patronizes": "patronises",
    "patronized": "patronised",
    "patronizing": "patronising",
    "plagiarize": "plagiarise",
    "plagiarizes": "plagiarises",
    "plagiarized": "plagiarised",
    "plagiarizing": "plagiarising",
    "romanticize": "romanticise",
    "romanticizes": "romanticises",
    "romanticized": "romanticised",
    "romanticizing": "romanticising",
    "scrutinize": "scrutinise",
    "scrutinizes": "scrutinises",
    "scrutinized": "scrutinised",
    "scrutinizing": "scrutinising",
    "victimize": "victimise",
    "victimizes": "victimises",
    "victimized": "victimised",
    "victimizing": "victimising",

    # -------------------------------------------------------------------------
    # -ization → -isation  (nouns + plurals where applicable)
    # -------------------------------------------------------------------------
    "authorization": "authorisation",
    "capitalization": "capitalisation",
    "categorization": "categorisation",
    "centralization": "centralisation",
    "characterization": "characterisation",
    "commercialization": "commercialisation",
    "conceptualization": "conceptualisation",
    "contextualization": "contextualisation",
    "crystallization": "crystallisation",
    "customization": "customisation",
    "decolonization": "decolonisation",
    "democratization": "democratisation",
    "destigmatization": "destigmatisation",
    "digitalization": "digitalisation",
    "digitization": "digitisation",
    "dramatization": "dramatisation",
    "equalization": "equalisation",
    "familiarization": "familiarisation",
    "fertilization": "fertilisation",
    "finalization": "finalisation",
    "formalization": "formalisation",
    "fossilization": "fossilisation",
    "generalizability": "generalisability",
    "generalization": "generalisation",
    "globalization": "globalisation",
    "harmonization": "harmonisation",
    "homogenization": "homogenisation",
    "idealization": "idealisation",
    "immunization": "immunisation",
    "incentivization": "incentivisation",
    "individualization": "individualisation",
    "industrialization": "industrialisation",
    "initialization": "initialisation",
    "institutionalization": "institutionalisation",
    "internalization": "internalisation",
    "legalization": "legalisation",
    "legitimization": "legitimisation",
    "localization": "localisation",
    "marginalization": "marginalisation",
    "maximization": "maximisation",
    "mechanization": "mechanisation",
    "medicalization": "medicalisation",
    "memorization": "memorisation",
    "minimization": "minimisation",
    "mobilization": "mobilisation",
    "modernization": "modernisation",
    "nationalization": "nationalisation",
    "naturalization": "naturalisation",
    "neutralization": "neutralisation",
    "normalization": "normalisation",
    "operationalization": "operationalisation",
    "optimization": "optimisation",
    "organization": "organisation",
    "organizations": "organisations",
    "penalization": "penalisation",
    "personalization": "personalisation",
    "polarization": "polarisation",
    "popularization": "popularisation",
    "prioritization": "prioritisation",
    "privatization": "privatisation",
    "problematization": "problematisation",
    "professionalization": "professionalisation",
    "radicalization": "radicalisation",
    "rationalization": "rationalisation",
    "realization": "realisation",
    "regularization": "regularisation",
    "reorganization": "reorganisation",
    "serialization": "serialisation",
    "socialization": "socialisation",
    "specialization": "specialisation",
    "stabilization": "stabilisation",
    "standardization": "standardisation",
    "sterilization": "sterilisation",
    "stigmatization": "stigmatisation",
    "subsidization": "subsidisation",
    "summarization": "summarisation",
    "symbolization": "symbolisation",
    "systematization": "systematisation",
    "trivialization": "trivialisation",
    "urbanization": "urbanisation",
    "utilization": "utilisation",
    "vaporization": "vaporisation",
    "visualization": "visualisation",
    "computerization": "computerisation",
    "victimization": "victimisation",
    "vocalization": "vocalisation",
    "programme": "program",
    "programmes": "programs",

    # -------------------------------------------------------------------------
    # -or → -our  (with inflections)
    # -------------------------------------------------------------------------
    "behavior": "behaviour",
    "behaviors": "behaviours",
    "behavioral": "behavioural",
    "behaviorally": "behaviourally",
    "misbehavior": "misbehaviour",
    "color": "colour",
    "colors": "colours",
    "colored": "coloured",
    "coloring": "colouring",
    "colorful": "colourful",
    "colorless": "colourless",
    "multicolored": "multicoloured",
    "candor": "candour",
    "clamor": "clamour",
    "clamors": "clamours",
    "demeanor": "demeanour",
    "demeanors": "demeanours",
    "endeavor": "endeavour",
    "endeavors": "endeavours",
    "favor": "favour",
    "favors": "favours",
    "favorable": "favourable",
    "favorably": "favourably",
    "unfavorable": "unfavourable",
    "unfavorably": "unfavourably",
    "disfavor": "disfavour",
    "favorite": "favourite",
    "favorites": "favourites",
    "favoritism": "favouritism",
    "flavor": "flavour",
    "flavors": "flavours",
    "harbor": "harbour",
    "harbors": "harbours",
    "harbored": "harboured",
    "harboring": "harbouring",
    "honor": "honour",
    "honors": "honours",
    "honorable": "honourable",
    "honorably": "honourably",
    "honorary": "honorary",
    "dishonor": "dishonour",
    "dishonorable": "dishonourable",
    "humor": "humour",
    "humors": "humours",
    "humorous": "humorous",
    "labor": "labour",
    "labors": "labours",
    "labored": "laboured",
    "laboring": "labouring",
    "neighbor": "neighbour",
    "neighbors": "neighbours",
    "neighborhood": "neighbourhood",
    "neighborhoods": "neighbourhoods",
    "neighboring": "neighbouring",
    "odor": "odour",
    "odors": "odours",
    "odorless": "odourless",
    "rumor": "rumour",
    "rumors": "rumours",
    "rumored": "rumoured",
    "parlor": "parlour",
    "parlors": "parlours",
    "savior": "saviour",
    "saviors": "saviours",
    "savor": "savour",
    "savors": "savours",
    "savored": "savoured",
    "savoring": "savouring",
    "savory": "savoury",
    "tumor": "tumour",
    "tumors": "tumours",
    "valor": "valour",
    "vapor": "vapour",
    "vapors": "vapours",
    "vigor": "vigour",
    "vigorous": "vigorous",
    "ardor": "ardour",
    "fervor": "fervour",
    "splendor": "splendour",
    "armor": "armour",
    "armors": "armours",
    "armored": "armoured",
    "armoring": "armouring",
    "glamor": "glamour",
    "glamorous": "glamorous",

    # -------------------------------------------------------------------------
    # -er → -re  (with inflections)
    # -------------------------------------------------------------------------
    "center": "centre",
    "centers": "centres",
    "centered": "centred",
    "centering": "centring",
    "centerpiece": "centrepiece",
    "fiber": "fibre",
    "fibers": "fibres",
    "liter": "litre",
    "liters": "litres",
    "meter": "metre",
    "meters": "metres",
    "millimeter": "millimetre",
    "millimeters": "millimetres",
    "centimeter": "centimetre",
    "centimeters": "centimetres",
    "kilometer": "kilometre",
    "kilometers": "kilometres",
    "theater": "theatre",
    "theaters": "theatres",
    "caliber": "calibre",
    "calibers": "calibres",
    "somber": "sombre",
    "luster": "lustre",
    "lackluster": "lacklustre",
    "ocher": "ochre",
    "scepter": "sceptre",
    "specter": "spectre",
    "specters": "spectres",
    "maneuver": "manoeuvre",
    "maneuvers": "manoeuvres",
    "maneuvered": "manoeuvred",
    "maneuvering": "manoeuvring",

    # -------------------------------------------------------------------------
    # -ense → -ence / -nse → -nce
    # -------------------------------------------------------------------------
    "defense": "defence",
    "defenses": "defences",
    "defensive": "defensive",
    "offense": "offence",
    "offenses": "offences",
    "pretense": "pretence",

    # -------------------------------------------------------------------------
    # US single-l → AU double-l
    # -------------------------------------------------------------------------
    "canceled": "cancelled",
    "canceling": "cancelling",
    "counseling": "counselling",
    "counselor": "counsellor",
    "counselors": "counsellors",
    "labeled": "labelled",
    "labeling": "labelling",
    "leveled": "levelled",
    "leveling": "levelling",
    "modeled": "modelled",
    "modeling": "modelling",
    "signaled": "signalled",
    "signaling": "signalling",
    "traveled": "travelled",
    "traveling": "travelling",
    "traveler": "traveller",
    "travelers": "travellers",
    "unraveled": "unravelled",
    "unraveling": "unravelling",
    "quarreled": "quarrelled",
    "quarreling": "quarrelling",

    # -------------------------------------------------------------------------
    # -ment
    # -------------------------------------------------------------------------
    "acknowledgment": "acknowledgement",
    "acknowledgments": "acknowledgements",

    # -------------------------------------------------------------------------
    # Colour / grey
    # -------------------------------------------------------------------------
    "gray": "grey",
    "grays": "greys",

    # -------------------------------------------------------------------------
    # -og → -ogue
    # -------------------------------------------------------------------------
    "catalog": "catalogue",
    "catalogs": "catalogues",
    "monolog": "monologue",

    # -------------------------------------------------------------------------
    # Science / element spelling
    # -------------------------------------------------------------------------
    "aluminum": "aluminium",
    "sulfur": "sulphur",
    "sulfate": "sulphate",
    "sulfates": "sulphates",
    "sulfide": "sulphide",
    "sulfides": "sulphides",
    "sulfuric": "sulphuric",
    "sulfurous": "sulphurous",

    # -------------------------------------------------------------------------
    # Specific word pairs
    # -------------------------------------------------------------------------
    "mold": "mould",
    "molds": "moulds",
    "molded": "moulded",
    "molding": "moulding",
    "skeptic": "sceptic",
    "skeptics": "sceptics",
    "skeptical": "sceptical",
    "skeptically": "sceptically",
    "skepticism": "scepticism",
    "plow": "plough",
    "plows": "ploughs",

    # -------------------------------------------------------------------------
    # Microcredential spellings
    # -------------------------------------------------------------------------
    "microcredentialing": "microcredentialling",
    "microcredentialed": "microcredentialled",
}

# Remove any entries where American == Australian (safety check)
AU_CORRECTIONS = {k: v for k, v in AU_CORRECTIONS.items() if k != v}

# Set of all correct AU forms — used as a guard so words already in AU
# spelling are never "corrected" a second time (e.g. "organised" stays).
_AU_FORMS: frozenset[str] = frozenset(v.lower() for v in AU_CORRECTIONS.values())

# Pre-compile one big pattern for fast scanning (word-boundary aware)
_PATTERN = re.compile(
    r"\b(" + "|".join(re.escape(w) for w in sorted(AU_CORRECTIONS, key=len, reverse=True)) + r")\b",
    re.IGNORECASE,
)


def _preserve_case(original: str, replacement: str) -> str:
    """Match the capitalisation of *original* when applying *replacement*."""
    if original.isupper():
        return replacement.upper()
    if original[0].isupper():
        return replacement[0].upper() + replacement[1:]
    return replacement


def _get_style_name(para_el: etree._Element) -> str:
    """Return the paragraph style name or empty string."""
    pPr = para_el.find(f"{WQ}pPr")
    if pPr is None:
        return ""
    pStyle = pPr.find(f"{WQ}pStyle")
    if pStyle is None:
        return ""
    return pStyle.get(f"{WQ}val", "")


def _para_text(para_el: etree._Element) -> str:
    """Return the plain text of a paragraph element."""
    return "".join(t.text or "" for t in para_el.iter(f"{WQ}t"))


def _is_references_heading(para_el: etree._Element) -> bool:
    """Return True if this paragraph is the References Heading 1."""
    style = _get_style_name(para_el)
    if style not in ("Heading 1", "Heading1"):
        return False
    return _para_text(para_el).strip().lower() in ("references", "reference list")


def _merge_adjacent_runs(para_el: etree._Element) -> None:
    """Merge consecutive plain <w:r> elements with identical formatting.

    Word can split a single word across multiple runs (e.g. after autocorrect
    or partial formatting edits), which prevents single-run regex matching.
    Removing <w:proofErr> markers first and then merging same-format adjacent
    runs rebuilds the whole word in one run so the pattern can find it.
    """
    # Strip spell/grammar proof markers — they're rendering hints only.
    for tag in (f"{WQ}proofErr", f"{WQ}bookmarkStart", f"{WQ}bookmarkEnd"):
        for el in para_el.findall(tag):
            para_el.remove(el)

    changed = True
    while changed:
        changed = False
        children = list(para_el)
        for i in range(len(children) - 1):
            curr = children[i]
            nxt = children[i + 1]
            if curr.tag != f"{WQ}r" or nxt.tag != f"{WQ}r":
                continue
            # Skip runs that live inside tracked-change wrappers.
            for node in (curr, nxt):
                p = node.getparent()
                if p is not None and p.tag in (f"{WQ}del", f"{WQ}ins"):
                    break
            else:
                curr_rpr = curr.find(f"{WQ}rPr")
                nxt_rpr = nxt.find(f"{WQ}rPr")
                curr_bytes = etree.tostring(curr_rpr) if curr_rpr is not None else b""
                nxt_bytes = etree.tostring(nxt_rpr) if nxt_rpr is not None else b""
                if curr_bytes != nxt_bytes:
                    continue
                curr_t = curr.find(f"{WQ}t")
                nxt_t = nxt.find(f"{WQ}t")
                if curr_t is None or nxt_t is None:
                    continue
                curr_t.text = (curr_t.text or "") + (nxt_t.text or "")
                curr_t.set("{http://www.w3.org/XML/1998/namespace}space", "preserve")
                para_el.remove(nxt)
                changed = True
                break


def _split_run_at_match(
    run_el: etree._Element,
    m: re.Match,
    australian: str,
    change_id: int,
    comment_id: int | None = None,
) -> int:
    """Replace *run_el* in-place with (before | del | ins | after) elements.

    Returns the next available change ID.
    """
    nsmap = {"w": W}
    t_el = run_el.find(f"{WQ}t")
    if t_el is None:
        return change_id

    full_text: str = t_el.text or ""
    start, end = m.start(), m.end()
    before_text = full_text[:start]
    matched_text = full_text[start:end]
    after_text = full_text[end:]
    corrected = _preserve_case(matched_text, australian)

    rPr = run_el.find(f"{WQ}rPr")
    parent = run_el.getparent()
    if parent is None:
        return change_id
    pos = list(parent).index(run_el)
    parent.remove(run_el)
    insert_at = pos

    def _text_run(text: str) -> etree._Element:
        r = etree.Element(f"{WQ}r", nsmap=nsmap)
        if rPr is not None:
            r.append(deepcopy(rPr))
        t = etree.SubElement(r, f"{WQ}t")
        t.text = text
        t.set("{http://www.w3.org/XML/1998/namespace}space", "preserve")
        return r

    if before_text:
        parent.insert(insert_at, _text_run(before_text))
        insert_at += 1

    if comment_id is not None:
        parent.insert(insert_at, _comment_range_start(comment_id))
        insert_at += 1

    # <w:del>
    del_el = etree.Element(f"{WQ}del", nsmap=nsmap)
    del_el.set(f"{WQ}id", str(change_id))
    del_el.set(f"{WQ}author", AUTHOR)
    del_el.set(f"{WQ}date", DATE)
    del_run = etree.SubElement(del_el, f"{WQ}r")
    if rPr is not None:
        del_run.append(deepcopy(rPr))
    del_t = etree.SubElement(del_run, f"{WQ}delText")
    del_t.text = matched_text
    if matched_text and (matched_text[0].isspace() or matched_text[-1].isspace()):
        del_t.set("{http://www.w3.org/XML/1998/namespace}space", "preserve")
    parent.insert(insert_at, del_el)
    insert_at += 1
    change_id += 1

    # <w:ins>
    ins_el = etree.Element(f"{WQ}ins", nsmap=nsmap)
    ins_el.set(f"{WQ}id", str(change_id))
    ins_el.set(f"{WQ}author", AUTHOR)
    ins_el.set(f"{WQ}date", DATE)
    ins_run = etree.SubElement(ins_el, f"{WQ}r")
    if rPr is not None:
        ins_run.append(deepcopy(rPr))
    ins_t = etree.SubElement(ins_run, f"{WQ}t")
    ins_t.text = corrected
    ins_t.set("{http://www.w3.org/XML/1998/namespace}space", "preserve")
    parent.insert(insert_at, ins_el)
    insert_at += 1
    change_id += 1

    if comment_id is not None:
        parent.insert(insert_at, _comment_range_end(comment_id))
        insert_at += 1
        parent.insert(insert_at, _comment_reference_run(comment_id))
        insert_at += 1

    if after_text:
        parent.insert(insert_at, _text_run(after_text))

    return change_id


def _apply_corrections_to_para(
    para_el: etree._Element,
    change_id: int,
    made: list[dict],
    comment_summaries: dict[tuple[str, str], dict],
    next_comment_id: int,
    summary_comment_id: int | None,
) -> tuple[int, int, int | None]:
    """Apply all AU spelling corrections to runs within a single paragraph."""
    _merge_adjacent_runs(para_el)
    changed = True
    while changed:
        changed = False
        # Quote-protection: matches inside `"..."` spans are skipped so
        # direct quotations retain the source's spelling. Recompute spans
        # each outer iteration because a prior rewrite shifts offsets.
        para_plain = "".join(
            (t.find(f"{WQ}t").text or "")
            for t in para_el
            if t.tag == f"{WQ}r" and t.find(f"{WQ}t") is not None
        )
        quote_spans = find_quote_spans(para_plain)
        run_offset = 0
        for child in list(para_el):
            if child.tag != f"{WQ}r":
                continue
            grandparent = child.getparent()
            if grandparent is not None and grandparent.tag in (f"{WQ}del", f"{WQ}ins"):
                continue
            t_el = child.find(f"{WQ}t")
            if t_el is None or not (t_el.text or "").strip():
                run_offset += len(t_el.text or "") if t_el is not None else 0
                continue
            run_text = t_el.text or ""
            # First non-quoted match. Walking finditer lets us skip past
            # a quoted occurrence and find a later unquoted one in the
            # same run on the same pass.
            m = None
            for cand in _PATTERN.finditer(run_text):
                ps = run_offset + cand.start()
                pe = run_offset + cand.end()
                if any(ps < e and s < pe for s, e in quote_spans):
                    continue
                m = cand
                break
            run_offset += len(run_text)
            if m:
                american_lower = m.group(0).lower()
                # Skip words that are already correct AU spellings.
                # _PATTERN is built from US-form keys, but this guard catches
                # any edge case where an AU form slips through.
                if american_lower in _AU_FORMS and american_lower not in AU_CORRECTIONS:
                    continue
                australian = AU_CORRECTIONS.get(american_lower, "")
                if not australian:
                    continue
                original_word = m.group(0)
                corrected_word = _preserve_case(original_word, australian)
                if corrected_word.lower() == original_word.lower():
                    continue  # already the correct form — no change needed
                key = (original_word.casefold(), corrected_word.casefold())
                summary = comment_summaries.get(key)
                comment_id = None
                if summary_comment_id is None:
                    summary_comment_id = next_comment_id
                    next_comment_id += 1
                    comment_id = summary_comment_id
                if summary is None:
                    comment_summaries[key] = {
                        "original": original_word,
                        "replacement": corrected_word,
                        "count": 1,
                    }
                else:
                    summary["count"] += 1
                change_id = _split_run_at_match(
                    child, m, australian, change_id, comment_id=comment_id
                )
                made.append({"original": original_word, "replacement": corrected_word})
                changed = True
                break
    return change_id, next_comment_id, summary_comment_id


def apply_au_spelling_corrections(
    input_path: str,
    output_path: str,
    next_change_id: int = 1,
) -> tuple[int, list[dict]]:
    """Scan every eligible paragraph and apply AU spelling tracked changes.

    Returns (next_change_id, corrections_made) where corrections_made is a list
    of {original, replacement} dicts for every substitution applied.
    """
    with zipfile.ZipFile(input_path, "r") as z:
        names = z.namelist()
        doc_xml = z.read("word/document.xml")
        rels_xml = z.read("word/_rels/document.xml.rels")
        ct_xml = z.read("[Content_Types].xml")
        has_comments = "word/comments.xml" in names
        comments_xml = z.read("word/comments.xml") if has_comments else None

    doc_root = etree.fromstring(doc_xml)
    made: list[dict] = []
    comment_summaries: dict[tuple[str, str], dict] = {}
    summary_comment_id: int | None = None

    if comments_xml:
        comments_root = etree.fromstring(comments_xml)
        existing = [
            int(el.get(f"{WQ}id", 0))
            for el in comments_root.findall(f"{WQ}comment")
        ]
        next_comment_id = max(existing, default=0) + 1
    else:
        comments_root = etree.Element(f"{WQ}comments", nsmap={"w": W})
        next_comment_id = 1

    # Zone-aware iteration: skips Acknowledgements/References AND every
    # paragraph in the shared skip-style set (headings, captions, ref entries,
    # front-matter labels). Replaces develop's _is_references_heading branch,
    # which only handled the References zone — captions inside the body and
    # the Acknowledgements section were still being spell-corrected.
    for para_el, zone in iter_paragraphs_with_zone(doc_root):
        if should_skip_paragraph(para_el, zone):
            continue
        plain_text = "".join(
            (t.text or "")
            for r in para_el.iter(f"{WQ}r")
            for t in r.findall(f"{WQ}t")
            if r.getparent() is not None and r.getparent().tag not in (f"{WQ}del", f"{WQ}ins")
        )
        if not _PATTERN.search(plain_text):
            continue
        next_change_id, next_comment_id, summary_comment_id = _apply_corrections_to_para(
            para_el,
            next_change_id,
            made,
            comment_summaries,
            next_comment_id,
            summary_comment_id,
        )

    if comment_summaries and summary_comment_id is not None:
        comments_root.append(
            _make_comment_element(
                summary_comment_id,
                _spelling_summary_comment_text(list(comment_summaries.values())),
            )
        )

    new_doc_xml = etree.tostring(doc_root, xml_declaration=True, encoding="UTF-8", standalone=True)
    has_spelling_comments = bool(comment_summaries)
    new_comments_xml = etree.tostring(
        comments_root, xml_declaration=True, encoding="UTF-8", standalone=True
    )
    new_rels_xml = _patch_rels(rels_xml) if has_spelling_comments else rels_xml
    new_ct_xml = _patch_content_types(ct_xml) if has_spelling_comments else ct_xml

    tmp = output_path + ".lang.tmp"
    try:
        with zipfile.ZipFile(input_path, "r") as zin, zipfile.ZipFile(tmp, "w", zipfile.ZIP_DEFLATED) as zout:
            for item in zin.infolist():
                if item.filename == "word/document.xml":
                    zout.writestr(item, new_doc_xml)
                elif item.filename == "word/_rels/document.xml.rels":
                    zout.writestr(item, new_rels_xml)
                elif item.filename == "[Content_Types].xml":
                    zout.writestr(item, new_ct_xml)
                elif item.filename == "word/comments.xml" and has_spelling_comments:
                    zout.writestr(item, new_comments_xml)
                else:
                    zout.writestr(item, zin.read(item.filename))
            if has_spelling_comments and not has_comments:
                zout.writestr("word/comments.xml", new_comments_xml)
        os.replace(tmp, output_path)
    except Exception:
        try:
            os.unlink(tmp)
        except OSError:
            pass
        raise

    return next_change_id, made
