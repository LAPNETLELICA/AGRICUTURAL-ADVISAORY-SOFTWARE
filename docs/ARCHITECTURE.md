# Architecture Backend2

Backend2 est exclusivement le service de connaissance agricole camerounaise.

- **Source canonique** : `BASE_CONNAISSANCES_AGRICOLES/`
- **Backend1** : raisonnement et recommandation finale
- **Backend de liaison** : adaptation/transport entre Backend1 et Backend2
- **Backend2** : lecture, validation, exposition, provenance, ingestion et versioning des connaissances

L'ancien `knowledge/` et le moteur `engine/` ne font plus partie de Backend2.

## Flux runtime

```text
Backend1 -> Knowledge Gateway -> Backend2 API -> BASE_CONNAISSANCES_AGRICOLES
```

## Flux futur de mise à jour

```text
MINADER / IRAD / FAO
  -> discover
  -> fetch
  -> snapshot
  -> extract
  -> normalize
  -> compare
  -> staging
  -> revue humaine
  -> validation
  -> release
  -> publication
```

Aucune donnée externe ne peut modifier directement la release active.
