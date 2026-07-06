import { ref } from 'vue'

export function useSaveRecipe() {
  const name = ref('')
  const recipeText = ref('')
  const isSaving = ref(false)
  const saveError = ref('')
  const saveMessage = ref('')

  async function saveRecipe() {
    if (!name.value.trim() || !recipeText.value.trim() || isSaving.value) return

    isSaving.value = true
    saveError.value = ''
    saveMessage.value = ''

    try {
      const response = await fetch('/api/recipes/save', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ name: name.value, recipe: recipeText.value }),
      })

      const body = await response.json().catch(() => null)

      if (!response.ok) {
        throw new Error(body?.detail || `Save failed with status ${response.status}`)
      }

      saveMessage.value = body?.message || 'Recipe saved successfully.'
      name.value = ''
      recipeText.value = ''
    } catch (error) {
      saveError.value =
        error instanceof Error ? error.message : 'Something went wrong while saving. Please try again.'
    } finally {
      isSaving.value = false
    }
  }

  return { name, recipeText, isSaving, saveError, saveMessage, saveRecipe }
}
