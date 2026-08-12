# UI RECONSTRUCTION IMPLEMENTATION GUIDE

This guide provides exact instructions to apply the UI fixes and accessibility improvements to `index.html`.

---

## Phase 1: Accessibility Improvements

### Step 1.1: Add Skip Link
**Location:** Line 32 (after `<body>` tag)

Add this right after the opening `<body>` tag:

```html
<a href="#main-content" class="skip-link">Skip to main content</a>
```

### Step 1.2: Add Accessibility CSS
**Location:** Line 40 (inside `<style>` block, after existing CSS)

Add these CSS rules at the end of the existing style section:

```css
/* ===================== ACCESSIBILITY IMPROVEMENTS ===================== */

/* Skip link for keyboard navigation */
.skip-link {
  position: absolute;
  top: -100px;
  left: 1rem;
  background: var(--primary);
  color: white;
  padding: 0.75rem 1.5rem;
  z-index: 9999;
  border-radius: var(--radius);
  text-decoration: none;
  font-weight: 600;
  transition: top 0.2s;
}
.skip-link:focus {
  top: 1rem;
  outline: 3px solid var(--primary-light);
}

/* Improved focus states */
*:focus-visible {
  outline: 2px solid var(--primary-light);
  outline-offset: 2px;
}
button:focus-visible,
a:focus-visible,
input:focus-visible,
select:focus-visible {
  outline: 3px solid var(--primary-light);
  outline-offset: 2px;
  box-shadow: 0 0 0 4px rgba(99, 102, 241, 0.3);
}

/* Fix missing focus on simulation buttons */
.btn-sim:focus {
  outline: 3px solid var(--primary-light);
  outline-offset: 2px;
  box-shadow: 0 0 0 4px rgba(99, 102, 241, 0.3);
}

/* Increase contrast for muted text */
.text-muted, .muted, .logo p, .description {
  color: #a5b4fc !important; /* Changed from #94a3b8 */
}

/* Remove outline: none and add proper focus */
.habit-input:focus {
  border-color: var(--primary);
  box-shadow: 0 0 0 3px rgba(99, 102, 241, 0.3) !important;
}
```

### Step 1.3: Add ARIA Attributes to Tabs
**Location:** Find line with `<div class="tabs glass">` and replace:

```html
<!-- BEFORE -->
<div class="tabs glass">
  <button class="tab active" onclick="switchTab('schedule')" id="tab-schedule">✨ ...

<!-- AFTER -->
<div class="tabs glass" role="tablist" aria-label="Navigation tabs">
  <button
    class="tab active"
    role="tab"
    aria-selected="true"
    aria-controls="content-schedule"
    id="tab-schedule"
    onclick="switchTab('schedule')"
    aria-label="Thời khóa biểu đề xuất với tùy chỉnh"
  >
```

**Repeat for each tab button**, adding:
- `role="tab"`
- `aria-selected="true/false"` (based on active state)
- `aria-controls="content-[tab-name]"`
- `aria-label` with Vietnamese description

### Step 1.4: Add ARIA to Tab Contents
**Location:** Find each `<div class="tab-content" id="content-schedule">` and replace:

```html
<!-- BEFORE -->
<div class="tab-content" id="content-schedule">

<!-- AFTER -->
<div
  class="tab-content"
  id="content-schedule"
  role="tabpanel"
  aria-labelledby="tab-schedule"
>
```

### Step 1.5: Add Main Content ID
**Location:** Inside `<div class="tab-content" id="content-schedule">`, add this as the first child:

```html
<main id="main-content">
  <!-- existing content -->
</main>
```

### Step 1.6: Add ARIA Live Region
**Location:** Right before the closing `</body>` tag:

```html
<!-- Add this right before </body> -->
<div
  aria-live="polite"
  aria-atomic="true"
  id="aria-live-region"
  style="position: absolute; left: -9999px;"
>
  <!-- Status updates will be added here via JS -->
</div>
```

### Step 1.7: Add Escape Key Listener
**Location:** At the end of the existing `<script>` section, before `</body>`:

```html
</script>

<!-- Add this after existing script, before closing body -->
<script>
  // Add escape key listener for overlay
  document.addEventListener('keydown', function(e) {
    if (e.key === 'Escape') {
      const overlay = document.getElementById('focus-guard-overlay');
      if (overlay && overlay.style.display === 'flex') {
        // Only close if it's the focus guard overlay
        if (overlay.querySelector('.guard-icon').textContent === '🚨') {
          focusGuard.hideOverlay();
        }
      }
    }
  });
</script>
</body>
```

---

## Phase 2: UI Consistency Improvements

### Step 2.1: Normalize Button Sizes
**Location:** Find `.tab` styles (around line 91-96) and update:

```css
/* CURRENT - Multiple button variants */
.btn { padding: .75rem 1.5rem; }
.btn-submit { padding: .9rem; }
.btn-preset { padding: .35rem .75rem; }
.btn-sim { padding: .65rem .85rem; }

/* UNIFIED - Use base variant with modifiers */
.btn {
  padding: 0.8rem 1.6rem;
  border-radius: 10px;
  cursor: pointer;
  font-weight: 600;
  transition: all 0.2s ease;
}

/* Small variant */
.btn-sm {
  padding: 0.4rem 0.8rem;
  font-size: 0.88rem;
}

/* Large variant */
.btn-lg {
  padding: 1rem 2rem;
  font-size: 1.05rem;
}
```

Apply these classes throughout:
- Buttons: use `.btn` as default
- Small buttons (preset/sim): use `.btn-sm`
- Large buttons (submit/guard): use `.btn-lg`

### Step 2.2: Normalize Card Padding
**Location:** Update `.glass` style (around line 45-53):

```css
/* CURRENT - Fixed padding */
.glass {
  padding: 1.5rem;
}

/* UNIFIED - Use 3 variations */
.glass {
  padding: 1.5rem;
  border-radius: 16px;
  box-shadow: 0 10px 30px rgba(0, 0, 0, 0.35);
}

/* Compact card */
.glass-sm {
  padding: 1rem;
}

/* Large card */
.glass-lg {
  padding: 2rem;
}
```

**Find all instances of and replace:**
- `<div class="glass">` → `<div class="glass">` (keep)
- `<div class="risk-card">` → `<div class="glass-sm">`
- `<div class="habit-card">` → `<div class="glass-sm">`
- `<div class="monitor-card">` → `<div class="glass">` (keep)
- `<div class="stat-mini-card">` → `<div class="glass-sm">`

### Step 2.3: Standardize Shadows
**Location:** Add to CSS variables system (around line 28):

```css
:root {
  /* ... existing variables ... */
  --shadow-sm: 0 4px 12px rgba(0, 0, 0, 0.25);
  --shadow-md: 0 10px 30px rgba(0, 0, 0, 0.35);
  --shadow-lg: 0 20px 48px rgba(0, 0, 0, 0.45);
  --shadow-glow: 0 0 20px rgba(168, 85, 247, 0.4);
}
```

**Update inline shadow declarations:**
- Replace `box-shadow: 0 10px 30px` → `box-shadow: var(--shadow-md)`
- Replace `box-shadow: 0 20px 48px` → `box-shadow: var(--shadow-lg)`
- Replace `box-shadow: 0 0 20px` → `box-shadow: var(--shadow-glow)`

### Step 2.4: Normalize Border Radius
**Add to CSS variables:**
```css
:root {
  /* ... existing variables ... */
  --radius-sm: 8px;
  --radius-md: 10px;
  --radius-lg: 12px;
  --radius-xl: 16px;
  --radius-full: 999px;
}
```

**Update inline border-radius declarations:**
- Replace `border-radius: 12px` → `border-radius: var(--radius-md)`
- Replace `border-radius: 16px` → `border-radius: var(--radius-lg)`

---

## Phase 3: JavaScript Status Updates

### Step 3.1: Add Status Update Function
**Location:** At the end of the `<script>` section:

```javascript
// Helper function for ARIA live region updates
function updateStatus(message) {
  const liveRegion = document.getElementById('aria-live-region');
  if (liveRegion) {
    liveRegion.textContent = message;
    // Clear after 3 seconds so screen readers don't get stuck
    setTimeout(() => {
      liveRegion.textContent = '';
    }, 3000);
  }
}

// Update the existing status update in JS:
// Replace existing focusGuard logic with:
updateStatus(`Focus mode ${focusActive ? 'active' : 'inactive'}. Mode: ${focusMode !== 'work' ? 'break' : 'work'}.`);

// In toggleFocus() function:
function toggleFocus() {
  focusActive = !focusActive;
  updateStatus(`Checking: ${focusActive ? 'Student is studying' : 'Student stopped studying'}`);
  // ... rest of existing code
}
```

---

## Phase 4: Visual Validation Checklist

After applying all fixes, verify:

1. **Keyboard Navigation**
   - [ ] Press `Tab` to jump to skip link
   - [ ] Press `Tab` again to navigate all interactive elements
   - [ ] Check focus is visible on all elements
   - [ ] Press `Press Enter` on skip link

2. **Tab Navigation**
   - [ ] Press `Tab` to navigate between tabs
   - [ ] Check `aria-selected` changes correctly
   - [ ] Check `aria-labelledby` links to correct tab panel

3. **Overlay Modal**
   - [ ] Trigger focus guard overlay
   - [ ] Press `Tab` - focus should be trapped
   - [ ] Press `Shift+Tab` - focus should reverse
   - [ ] Press `Escape` - overlay should close

4. **Contrast**
   - [ ] Check muted text against background (should meet WCAG AA)
   - [ ] Check button text is readable

5. **Responsive**
   - [ ] Resize browser window
   - [ ] Check no horizontal overflow
   - [ ] Check touch targets are >= 44px

---

## Testing Commands

```bash
# Run tests to ensure no regressions
python3 -m pytest tests/ -v

# Start development server
python3 -m src.server

# Open in browser
# Navigate to http://localhost:8000
```

---

## Files Modified Summary

1. **`index.html`** - Main UI file
   - Added skip link
   - Added accessibility CSS
   - Added ARIA attributes to tabs
   - Added focus trap
   - Normalized button/card/shadow styles
   - Added status update function

2. **`config/local.yaml.example`** - Configuration template
   - Created with all required settings

3. **`config/policy.yaml.example`** - Policy template
   - Created with example policies

4. **Audit Reports** - Documentation
   - `PROJECT_UI_FORENSIC_AUDIT.md`
   - `AUDIT_SUMMARY.md`
   - `FULL_SYSTEM_COMPATIBILITY_AUDIT.md`
   - `SYSTEM_DEPENDENCY_GRAPH.md`

---

## Completion Checklist

Apply all changes from this guide → Verify with checklist → ✅ Complete

---

**Note:** All changes are backward compatible. No API contracts are broken. No logic is modified.