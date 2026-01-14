import { ref, onMounted } from 'vue'

export const useTheme = () => {
  const currentTheme = ref('light')

  const setTheme = (theme: string) => {
    currentTheme.value = theme
    document.body.setAttribute('data-theme', theme)
    localStorage.setItem('theme', theme)
  }

  const loadTheme = () => {
    const savedTheme = localStorage.getItem('theme') || 'light'
    setTheme(savedTheme)
  }

  onMounted(() => {
    loadTheme()
  })

  return {
    currentTheme,
    setTheme
  }
}
