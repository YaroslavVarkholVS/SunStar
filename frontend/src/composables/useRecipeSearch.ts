import { computed, ref } from 'vue'
import { parseNdjsonStream } from '../lib/ndjsonStream'

type StreamEvent =
  | { type: 'token'; content: string }
  | { type: 'done' }
  | { type: 'error'; detail: string }

export function useRecipeSearch() {
  const ingredients = ref('')
  const rawText = ref('')
  const isSearching = ref(false)
  const errorMessage = ref('')
  let abortController: AbortController | null = null

  const recipes = computed(() =>
    rawText.value
      .split('\n')
      .map((recipe) => recipe.trim())
      .filter(Boolean),
  )

  async function searchRecipes() {
    if (!ingredients.value.trim() || isSearching.value) return

    isSearching.value = true
    errorMessage.value = ''
    rawText.value = ''
    abortController = new AbortController()

    try {
      const response = await fetch('/api/recipes/search', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ ingredients: ingredients.value }),
        signal: abortController.signal,
      })

      if (!response.ok || !response.body) {
        const body = await response.json().catch(() => null)
        throw new Error(body?.detail || `Search failed with status ${response.status}`)
      }

      for await (const event of parseNdjsonStream<StreamEvent>(response.body)) {
        if (event.type === 'token') {
          rawText.value += event.content
        } else if (event.type === 'error') {
          throw new Error(event.detail)
        }
      }
    } catch (error) {
      if (error instanceof DOMException && error.name === 'AbortError') return
      console.error('Error searching recipes:', error)
      errorMessage.value =
        error instanceof Error ? error.message : 'Something went wrong while searching. Please try again.'
      rawText.value = ''
    } finally {
      isSearching.value = false
      abortController = null
    }
  }

  function cancelSearch() {
    abortController?.abort()
  }

  return { ingredients, recipes, isSearching, errorMessage, searchRecipes, cancelSearch }
}