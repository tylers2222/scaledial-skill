# ML inference service for document classification

Team: 4 engineers. Customers send documents through an API and get labels back. Scale range to explain: 5,000 documents per day up to 20 million per day.

Components:
- Public API that accepts documents (average 200 KB) and returns labels.
- Model serving on GPUs. One model, about 7 billion parameters.
- Request batching in front of the model.
- Queue for large customer uploads that do not need an immediate answer.
- Storage of inputs and outputs for 30 days for debugging and retraining.
- Usage metering and billing per customer.
- Model rollout: new versions every 2 weeks, with a comparison against the old version.
