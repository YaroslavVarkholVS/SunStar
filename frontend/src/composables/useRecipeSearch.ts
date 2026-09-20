import { computed, ref } from 'vue'
import { parseNdjsonStream } from '../lib/ndjsonStream'

type RecipeApprovalInterrupt = {
  type: 'recipe_approval'
  question: string
  recipe: string
}

type StreamEvent =
  | {
      type: 'started'
      thread_id: string
    }
  | {
      type: 'token'
      content: string
    }
  | {
      type: 'interrupt'
      interrupt_id: string
      data: RecipeApprovalInterrupt
    }
  | {
      type: 'done'
    }
  | {
      type: 'error'
      detail: string
    }

export function useRecipeSearch() {
  const ingredients = ref('')
  const rawText = ref('')
  const isSearching = ref(false)
  const errorMessage = ref('')

  // LangGraph thread that can be resumed later.
  const threadId = ref<string | null>(null)

  // Non-null means LangGraph is currently paused
  // at interrupt().
  const pendingApproval = ref<{
    interruptId: string
    question: string
    recipe: string
  } | null>(null)

  const isWaitingForApproval = computed(
    () => pendingApproval.value !== null,
  )

  let abortController: AbortController | null = null

  const recipes = computed(() =>
    rawText.value
      .split('\n')
      .map((recipe) => recipe.trim())
      .filter(Boolean),
  )

  async function searchRecipes() {
    if (!ingredients.value.trim() || isSearching.value) {
      return
    }

    isSearching.value = true
    errorMessage.value = ''
    rawText.value = ''
    threadId.value = null
    pendingApproval.value = null

    abortController = new AbortController()

    try {
      const response = await fetch('/api/recipes/search', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          ingredients: ingredients.value,
        }),
        signal: abortController.signal,
      })

      if (!response.ok || !response.body) {
        const body = await response.json().catch(() => null)

        throw new Error(
          body?.detail ||
            `Search failed with status ${response.status}`,
        )
      }

      for await (const event of parseNdjsonStream<StreamEvent>(
        response.body,
      )) {
        if (event.type === 'started') {
          threadId.value = event.thread_id
        } else if (event.type === 'token') {
          rawText.value += event.content
        } else if (event.type === 'interrupt') {
          pendingApproval.value = {
            interruptId: event.interrupt_id,
            question: event.data.question,
            recipe: event.data.recipe,
          }
        } else if (event.type === 'error') {
          throw new Error(event.detail)
        }
      }
    } catch (error) {
      if (
        error instanceof DOMException &&
        error.name === 'AbortError'
      ) {
        return
      }

      console.error('Error searching recipes:', error)

      errorMessage.value =
        error instanceof Error
          ? error.message
          : 'Something went wrong while searching. Please try again.'

      rawText.value = ''
      pendingApproval.value = null
    } finally {
      isSearching.value = false
      abortController = null
    }
  }

  async function resumeRecipe(approved: boolean) {
    if (!threadId.value || !pendingApproval.value) {
      console.error(
        'Cannot resume recipe search: no thread ID or pending approval.',
      )
      return
    }

    const currentThreadId = threadId.value

    // Hide the approval UI immediately.
    pendingApproval.value = null

    isSearching.value = true
    errorMessage.value = ''

    abortController = new AbortController()

    try {
      const response = await fetch(
        '/api/recipes/search/resume',
        {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({
            thread_id: currentThreadId,
            approved,
          }),
          signal: abortController.signal,
        },
      )

      if (!response.ok || !response.body) {
        const body = await response.json().catch(() => null)

        throw new Error(
          body?.detail ||
            `Resume failed with status ${response.status}`,
        )
      }

      for await (const event of parseNdjsonStream<StreamEvent>(
        response.body,
      )) {
        if (event.type === 'token') {
          rawText.value += event.content
        } else if (event.type === 'interrupt') {
          pendingApproval.value = {
            interruptId: event.interrupt_id,
            question: event.data.question,
            recipe: event.data.recipe,
          }
        } else if (event.type === 'error') {
          throw new Error(event.detail)
        }
      }
    } catch (error) {
      if (
        error instanceof DOMException &&
        error.name === 'AbortError'
      ) {
        return
      }

      console.error(
        'Error resuming recipe search:',
        error,
      )

      errorMessage.value =
        error instanceof Error
          ? error.message
          : 'Something went wrong while continuing the recipe search.'

      pendingApproval.value = null
    } finally {
      isSearching.value = false
      abortController = null
    }
  }

  function cancelSearch() {
    abortController?.abort()
  }

  return {
    ingredients,
    recipes,
    isSearching,
    isWaitingForApproval,
    pendingApproval,
    errorMessage,
    searchRecipes,
    resumeRecipe,
    cancelSearch,
  }
}