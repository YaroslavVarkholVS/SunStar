<script setup lang="ts">
import { useSaveRecipe } from '../composables/useSaveRecipe'

const { name, recipeText, isSaving, saveError, saveMessage, saveRecipe } = useSaveRecipe()
</script>

<template>
  <section class="save-section">
    <h2>Add your own recipe</h2>
    <p class="subtitle">Have a recipe of your own? Save it so it can be found in future searches.</p>

    <form class="save-form" @submit.prevent="saveRecipe">
      <input v-model="name" type="text" placeholder="Recipe name" aria-label="Recipe name" />
      <textarea
        v-model="recipeText"
        rows="6"
        placeholder="Type or paste the recipe here"
        aria-label="Recipe text"
      />
      <button type="submit" :disabled="isSaving">
        {{ isSaving ? 'Saving…' : 'Save recipe' }}
      </button>
    </form>

    <p v-if="saveError" class="error">{{ saveError }}</p>
    <p v-if="saveMessage" class="success">{{ saveMessage }}</p>
  </section>
</template>
