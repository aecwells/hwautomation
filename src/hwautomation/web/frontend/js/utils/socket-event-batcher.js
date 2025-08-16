/**
 * Socket Event Batcher
 *
 * Batches rapid Socket.IO events to prevent UI flooding and improve performance.
 * Useful for high-frequency workflow progress updates.
 */

class SocketEventBatcher {
  constructor(options = {}) {
    this.batchDelay = options.batchDelay || 100; // ms
    this.maxBatchSize = options.maxBatchSize || 50;
    this.batches = new Map();
    this.timers = new Map();
  }

  /**
   * Add an event to be batched
   */
  addEvent(eventType, data) {
    const batchKey = this.getBatchKey(eventType, data);

    if (!this.batches.has(batchKey)) {
      this.batches.set(batchKey, []);
    }

    const batch = this.batches.get(batchKey);
    batch.push({
      timestamp: Date.now(),
      data
    });

    // Limit batch size
    if (batch.length > this.maxBatchSize) {
      batch.shift(); // Remove oldest
    }

    this.scheduleBatchFlush(batchKey, eventType);
  }

  /**
   * Get batch key for grouping similar events
   */
  getBatchKey(eventType, data) {
    switch (eventType) {
      case 'workflow_progress_update':
        return `workflow_progress:${data.workflow_id}`;
      case 'workflow_step_update':
        return `workflow_step:${data.workflow_id}`;
      case 'server_status_update':
        return `server_status:${data.server_id}`;
      case 'activity_update':
        return 'activity_batch';
      default:
        return eventType;
    }
  }

  /**
   * Schedule batch to be flushed
   */
  scheduleBatchFlush(batchKey, eventType) {
    // Clear existing timer
    if (this.timers.has(batchKey)) {
      clearTimeout(this.timers.get(batchKey));
    }

    // Schedule new flush
    const timer = setTimeout(() => {
      this.flushBatch(batchKey, eventType);
    }, this.batchDelay);

    this.timers.set(batchKey, timer);
  }

  /**
   * Flush a batch of events
   */
  flushBatch(batchKey, eventType) {
    const batch = this.batches.get(batchKey);

    if (!batch || batch.length === 0) {
      return;
    }

    // Get the most recent event (for progress updates)
    const latestEvent = batch[batch.length - 1];

    // For some events, we want all events, for others just the latest
    const eventsToFlush = this.shouldBatchAll(eventType) ? batch : [latestEvent];

    // Emit batched event
    this.emitBatchedEvent(eventType, eventsToFlush, batchKey);

    // Clean up
    this.batches.delete(batchKey);
    this.timers.delete(batchKey);
  }

  /**
   * Determine if we should include all events or just the latest
   */
  shouldBatchAll(eventType) {
    return ['activity_update'].includes(eventType);
  }

  /**
   * Emit the batched event
   */
  emitBatchedEvent(eventType, events, batchKey) {
    const customEvent = new CustomEvent(`batched:${eventType}`, {
      detail: {
        events,
        batchKey,
        eventCount: events.length,
        batchedAt: Date.now()
      }
    });

    document.dispatchEvent(customEvent);
  }

  /**
   * Force flush all pending batches
   */
  flushAll() {
    for (const [batchKey, timer] of this.timers) {
      clearTimeout(timer);

      // Determine event type from batch key
      const eventType = batchKey.split(':')[0].replace('_batch', '_update');
      this.flushBatch(batchKey, eventType);
    }
  }

  /**
   * Clear all batches
   */
  clear() {
    for (const timer of this.timers.values()) {
      clearTimeout(timer);
    }

    this.batches.clear();
    this.timers.clear();
  }
}

export { SocketEventBatcher };
