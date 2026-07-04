<script setup lang="ts">
import { ref } from 'vue'

interface RecipeSearchResponse {
  recipes: string[]
}

const ingredients = ref('')
const recipes = ref<string[]>([])
const isSearching = ref(false)
const errorMessage = ref('')

async function searchRecipes() {
  if (!ingredients.value.trim()) return

  isSearching.value = true
  errorMessage.value = ''

  try {
    const response = await fetch('/api/recipes/search', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ ingredients: ingredients.value }),
    })

    if (!response.ok) {
      const body = await response.json().catch(() => null)
      throw new Error(body?.detail || `Search failed with status ${response.status}`)
    }

    const data: RecipeSearchResponse = await response.json()
    recipes.value = data.recipes
  } catch (error) {
    console.error('Error searching recipes:', error)
    errorMessage.value =
      error instanceof Error ? error.message : 'Something went wrong while searching. Please try again.'
    recipes.value = []
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
