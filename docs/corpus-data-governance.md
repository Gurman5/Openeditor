# Corpus Data Governance

This document explains how documents used in the Track K evaluation corpus should be stored and handled.

The corpus includes test documents from different sources, including public APA examples and assignments owned by members of the project team. Because some of these documents may contain personal information, they should not automatically be committed to the Git repository.

## Purpose

The purpose of these rules is to make sure that the evaluation corpus can be used for testing without accidentally exposing personal or copyrighted documents.

The corpus should still be reproducible, but sensitive documents should stay outside the repository where possible.

## Real student documents

Team-owned assignments are stored under:

```text
tests/corpus/real/