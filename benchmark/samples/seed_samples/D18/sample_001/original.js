/**
 * Priority Queue with Weighted Scheduling
 *
 * Implements a min-heap-based priority queue where items have both a
 * priority value and a weight. Items with lower priority values are
 * dequeued first. When multiple items share the same priority, the
 * one with higher weight is preferred.
 *
 * Use case: Task scheduler where priority determines urgency and
 * weight determines the amount of resources allocated.
 */

class PriorityQueue {
    constructor() {
        this._heap = [];
    }

    /**
     * Get the number of items in the queue.
     */
    get size() {
        return this._heap.length;
    }

    /**
     * Check if the queue is empty.
     */
    get isEmpty() {
        return this._heap.length === 0;
    }

    /**
     * Peek at the highest-priority item without removing it.
     */
    peek() {
        if (this.isEmpty) return null;
        return this._heap[0];
    }

    /**
     * Enqueue an item with a given priority and weight.
     * @param {*} value - The item to enqueue
     * @param {number} priority - Lower values = higher priority
     * @param {number} weight - Higher values = preferred among same priority
     */
    enqueue(value, priority, weight) {
        const node = { value, priority, weight: weight || 0 };
        this._heap.push(node);
        this._bubbleUp(this._heap.length - 1);
    }

    /**
     * Dequeue the highest-priority item.
     * @returns {*} The value of the dequeued item, or null if empty.
     */
    dequeue() {
        if (this.isEmpty) return null;

        const top = this._heap[0];
        const last = this._heap.pop();

        if (this._heap.length > 0) {
            this._heap[0] = last;
            this._sinkDown(0);
        }

        return top.value;
    }

    /**
     * Schedule items by weight: returns items in priority order,
     * but within the same priority level, higher-weight items come first.
     */
    weightedSchedule() {
        const sorted = [...this._heap].sort((a, b) => {
            if (a.priority !== b.priority) {
                return a.priority - b.priority;
            }
            return b.weight - a.weight;
        });
        return sorted.map(item => item.value);
    }

    _bubbleUp(index) {
        while (index > 0) {
            const parentIndex = Math.floor((index - 1) / 2);
            if (this._compare(index, parentIndex) < 0) {
                this._swap(index, parentIndex);
                index = parentIndex;
            } else {
                break;
            }
        }
    }

    _sinkDown(index) {
        const length = this._heap.length;
        while (true) {
            const leftChild = 2 * index + 1;
            const rightChild = 2 * index + 2;
            let smallest = index;

            if (leftChild < length && this._compare(leftChild, smallest) < 0) {
                smallest = leftChild;
            }
            if (rightChild < length && this._compare(rightChild, smallest) < 0) {
                smallest = rightChild;
            }

            if (smallest !== index) {
                this._swap(index, smallest);
                index = smallest;
            } else {
                break;
            }
        }
    }

    _compare(i, j) {
        const a = this._heap[i];
        const b = this._heap[j];
        if (a.priority !== b.priority) {
            return a.priority - b.priority;
        }
        return b.weight - a.weight;
    }

    _swap(i, j) {
        const temp = this._heap[i];
        this._heap[i] = this._heap[j];
        this._heap[j] = temp;
    }
}

module.exports = { PriorityQueue };
