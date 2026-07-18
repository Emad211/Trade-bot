# Phase 3H bounded diversified AvalAI pilot evidence

This directory records compact evidence from the first successful live Phase 3H
source-diversity pilot. No secret material or trading decision is included.

## Identity

- Workflow run: `29645401163`
- Source commit: `824d13d51de2bdd302454fe36a7f0a945966cc91`
- Artifact ID: `8429886030`
- Artifact digest: `sha256:ec077f99caadaa28fc3142a9482b4f6160f4a338759692341825719d241fad91`
- Assessment ID: `e26acb5aeca8ecf8e9d952e8863fa805d8b1a3907f897d8dc0853aac2ca7d02f`

## Restored state

The pilot restored and verified compact Phase 3E state from workflow run
`29575275480`, artifact `8404763802`, with digest
`sha256:41a4afc354faecd4cbbad2a7ef55e6f00e21d48eb904bf4b0f8d8d5cf0f05ba8`.
The document, semantic and provider-call ledgers passed verification before new
retrieval or inference.

## Feed and relevance result

All five configured feeds were retrieved successfully.

- Bitcoin Core: 10 accepted documents;
- Geth: 10 accepted documents;
- Bitcoin Optech: 8 accepted documents;
- Federal Reserve monetary policy: 10 accepted documents;
- SEC press releases: 20 rejected documents and zero accepted documents.

The SEC source therefore consumed no provider call. Relevance decisions were
persisted and included in the capture checksum inventory.

## Provider delta

The hard source-round-robin budget produced exactly four new calls:

- Bitcoin Core to BTC;
- Geth to ETH;
- Bitcoin Optech to BTC;
- Federal Reserve to MARKET.

All four calls succeeded on their first attempt with the pinned
`gpt-5-mini-2025-08-07` Responses API contract.

- input tokens: 4,059;
- output tokens: 387;
- total tokens: 4,446 of the 8,000-token ceiling;
- mean latency: 3.47 seconds;
- maximum latency: 4.78 seconds;
- failed calls: 0;
- duplicate extraction keys: 0;
- zero-accepted sources called: 0.

The new semantic delta contained four independent sources and three assets. Required
Bitcoin Optech, Federal Reserve, BTC and MARKET coverage all passed.

## Independent audit

After downloading the artifact, all 27 top-level checksum records and all six nested
capture/provider checksum inventories were verified. Restored-state provenance,
provider/capture linkage, call-to-semantic mapping, relevance totals, the empty
prospective decision ledger and the absence of credential-shaped material were also
verified.

Raw feed payloads and provider trace metadata remain in the digest-addressed GitHub
Actions artifact rather than Git history.

## Interpretation

The passing result permits continued diversified prospective semantic collection
only. It does not establish predictive value, alpha, calibration or economic utility,
and it does not authorize additional unbounded provider activity, model fitting,
paper trading or live trading.
