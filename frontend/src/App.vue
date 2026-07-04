<script setup lang="ts">
import { computed, ref } from 'vue'

type StreamEvent =
  | { type: 'token'; content: string }
  | { type: 'done' }
  | { type: 'error'; detail: string }

const ingredients = ref('')
const rawText = ref('')
const isSearching = ref(false)
const errorMessage = ref('')

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

  try {
    const response = await fetch('/api/recipes/search', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ ingredients: ingredients.value }),
    })

    if (!response.ok || !response.body) {
      const body = await response.json().catch(() => null)
      throw new Error(body?.detail || `Search failed with status ${response.status}`)
    }

    const reader = response.body.getReader()
    const decoder = new TextDecoder()
    let buffer = ''

    while (true) {
      const { done, value } = await reader.read()
      if (done) break
      buffer += decoder.decode(value, { stream: true })

      let newlineIndex
      while ((newlineIndex = buffer.indexOf('\n')) !== -1) {
        const line = buffer.slice(0, newlineIndex)
        buffer = buffer.slice(newlineIndex + 1)
        if (!line.trim()) continue

        const event: StreamEvent = JSON.parse(line)
        if (event.type === 'token') {
          rawText.value += event.content
        } else if (event.type === 'error') {
          throw new Error(event.detail)
        }
      }
    }
  } catch (error) {
    console.error('Error searching recipes:', error)
    errorMessage.value =
      error instanceof Error ? error.message : 'Something went wrong while searching. Please try again.'
    rawText.value = ''
  } finally {
    isSearching.value = false
  }
}
</script>

<template>
  <main id="app">
    <h1>SunStar Recipes</h1>
    <p class="subtitle">Enter the ingredients you have, and we'll find recipes for you.</p>

    <form class="search-form" @submit.prevent="searchRecipes">
      <input
        v-model="ingredients"
        type="text"
        placeholder="e.g. chicken, rice, tomatoes"
        aria-label="Ingredients"
      />
      <button type="submit" :disabled="isSearching">
        {{ isSearching ? 'Searching…' : 'Search' }}
      </button>
    </form>

    <p v-if="errorMessage" class="error">{{ errorMessage }}</p>

    <ul v-if="recipes.length" class="results">
      <li v-for="recipe in recipes" :key="recipe">{{ recipe }}</li>
    </ul>
    <p v-else-if="!isSearching && !errorMessage" class="empty-state">
      No recipes yet — try searching for some ingredients.
    </p>
  </main>
</template>