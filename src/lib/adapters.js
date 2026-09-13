/** Future adapters. Phase 1 does not send data to an AI service or claim measured mastery. */
export const masteryAdapter = {
  async getMastery(_learnerId) { return { status:'not_connected', records:[] } },
  async saveEvidence(_evidence) { return { status:'not_connected' } }
}
export const tutorAdapter = {
  async ask({ nodeId, question, sourceIds }) {
    if(!nodeId || !question || !Array.isArray(sourceIds)) throw new TypeError('nodeId, question and sourceIds are required')
    return { status:'not_connected', answer:null, citations:[] }
  }
}
