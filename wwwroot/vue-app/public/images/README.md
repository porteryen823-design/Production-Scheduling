# Images Directory

This directory is for storing static images used in the Vue app.

## Usage

Place your image files (PNG, JPG, GIF, SVG, etc.) in this directory.

In Vue components, reference images using:

```vue
<template>
  <img src="/images/your-image.png" alt="Description" />
</template>
```

The `/images/` path maps to this directory in the built application.

## Organization

You can create subdirectories for better organization:

- `/images/icons/` - Icon files
- `/images/logos/` - Logo files
- `/images/charts/` - Chart images
- `/images/uploads/` - User uploaded images

## Notes

- Images in this directory are served as static assets
- They are not processed by Vite's build system
- File names should be URL-safe (no spaces, special characters)
- Consider optimizing images for web (compression, appropriate formats)