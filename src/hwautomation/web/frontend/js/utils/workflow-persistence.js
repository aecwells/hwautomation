/**
 * Workflow Persistence Utilities
 *
 * Handles saving and restoring workflow progress to localStorage
 * for better user experience during page refreshes or disconnections.
 */

class WorkflowPersistence {
  constructor() {
    this.keyPrefix = 'hwautomation_workflow_';
    this.maxStorageAge = 24 * 60 * 60 * 1000; // 24 hours
  }

  /**
   * Save workflow progress to localStorage
   */
  saveProgress(workflowId, progressData) {
    try {
      const data = {
        ...progressData,
        timestamp: Date.now(),
        workflowId
      };

      const key = this.keyPrefix + workflowId;
      localStorage.setItem(key, JSON.stringify(data));

      console.debug(`Saved progress for workflow ${workflowId}`);
    } catch (error) {
      console.warn('Failed to save workflow progress:', error);
    }
  }

  /**
   * Restore workflow progress from localStorage
   */
  restoreProgress(workflowId) {
    try {
      const key = this.keyPrefix + workflowId;
      const saved = localStorage.getItem(key);

      if (!saved) {
        return null;
      }

      const data = JSON.parse(saved);

      // Check if data is too old
      if (Date.now() - data.timestamp > this.maxStorageAge) {
        this.removeProgress(workflowId);
        return null;
      }

      console.debug(`Restored progress for workflow ${workflowId}`);
      return data;
    } catch (error) {
      console.warn('Failed to restore workflow progress:', error);
      return null;
    }
  }

  /**
   * Remove workflow progress from localStorage
   */
  removeProgress(workflowId) {
    try {
      const key = this.keyPrefix + workflowId;
      localStorage.removeItem(key);
      console.debug(`Removed progress for workflow ${workflowId}`);
    } catch (error) {
      console.warn('Failed to remove workflow progress:', error);
    }
  }

  /**
   * Get all stored workflow IDs
   */
  getAllWorkflowIds() {
    const workflowIds = [];

    try {
      for (let i = 0; i < localStorage.length; i++) {
        const key = localStorage.key(i);
        if (key && key.startsWith(this.keyPrefix)) {
          const workflowId = key.substring(this.keyPrefix.length);
          workflowIds.push(workflowId);
        }
      }
    } catch (error) {
      console.warn('Failed to get stored workflow IDs:', error);
    }

    return workflowIds;
  }

  /**
   * Clean up old workflow progress data
   */
  cleanup() {
    const workflowIds = this.getAllWorkflowIds();
    let cleanedCount = 0;

    workflowIds.forEach(workflowId => {
      const progress = this.restoreProgress(workflowId);
      if (!progress) {
        // Already cleaned up by restoreProgress if too old
        cleanedCount++;
      }
    });

    if (cleanedCount > 0) {
      console.log(`Cleaned up ${cleanedCount} old workflow progress entries`);
    }
  }

  /**
   * Get workflow progress summary
   */
  getProgressSummary(workflowId) {
    const progress = this.restoreProgress(workflowId);

    if (!progress) {
      return null;
    }

    return {
      workflowId,
      status: progress.status,
      progress: progress.progress,
      currentStep: progress.current_step,
      savedAt: new Date(progress.timestamp).toLocaleString(),
      isStale: Date.now() - progress.timestamp > 5 * 60 * 1000 // 5 minutes
    };
  }
}

export { WorkflowPersistence };
