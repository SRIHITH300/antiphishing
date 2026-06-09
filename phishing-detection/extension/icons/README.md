# Extension Icons

This directory should contain the extension icons in three sizes:

## Required Files:

1. **icon16.png** (16x16 pixels)
   - Used in extension toolbar
   - PNG format
   - Transparent background recommended

2. **icon48.png** (48x48 pixels)
   - Used in extension management page
   - PNG format
   - Transparent background recommended

3. **icon128.png** (128x128 pixels)
   - Used in Chrome Web Store
   - PNG format
   - Transparent background recommended

## Design Guidelines:

- **Color Scheme**: Use blue/purple gradient (matches the extension theme)
- **Symbol**: Shield icon or security-related imagery
- **Style**: Modern, clean, professional
- **Background**: Transparent or gradient

## Quick Creation:

You can create these icons using:
- Design tools: Figma, Sketch, Adobe Illustrator
- Online generators: favicon.io, realfavicongenerator.net
- AI tools: Midjourney, DALL-E (generate shield icon)

## Example SVG Code:

```svg
<svg width="128" height="128" viewBox="0 0 128 128" xmlns="http://www.w3.org/2000/svg">
  <defs>
    <linearGradient id="gradient" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" style="stop-color:#667eea;stop-opacity:1" />
      <stop offset="100%" style="stop-color:#764ba2;stop-opacity:1" />
    </linearGradient>
  </defs>
  
  <!-- Shield shape -->
  <path d="M64 10 L100 30 L100 70 Q100 90 64 110 Q28 90 28 70 L28 30 Z" 
        fill="url(#gradient)" stroke="#fff" stroke-width="3"/>
  
  <!-- Checkmark -->
  <path d="M50 64 L58 72 L78 52" 
        stroke="#fff" stroke-width="6" fill="none" 
        stroke-linecap="round" stroke-linejoin="round"/>
</svg>
```

Convert this SVG to PNG at different sizes for the icons.

## Temporary Placeholder:

If you don't have icons yet, you can:
1. Use any 16x16, 48x48, 128x128 PNG images
2. The extension will still work, just with placeholder icons
3. Update icons later by replacing files and reloading extension

## Notes:

- Icons are not committed to git (in .gitignore)
- Create icons before publishing to Chrome Web Store
- Ensure high quality at all sizes (no pixelation)
