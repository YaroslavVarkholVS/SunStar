<script setup lang="ts">
import { onUnmounted } from 'vue'
import { useRecipeSearch } from './composables/useRecipeSearch'
import SaveRecipeForm from './components/SaveRecipeForm.vue'

const { ingredients, recipes, isSearching, errorMessage, searchRecipes, cancelSearch } = useRecipeSearch()

onUnmounted(cancelSearch)
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

    <SaveRecipeForm />
  </main>
</template>