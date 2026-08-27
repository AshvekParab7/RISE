---
name: Tactile Intelligence
colors:
  surface: '#f4fbfa'
  surface-dim: '#d4dbda'
  surface-bright: '#f4fbfa'
  surface-container-lowest: '#ffffff'
  surface-container-low: '#eef5f4'
  surface-container: '#e8efee'
  surface-container-high: '#e3eae8'
  surface-container-highest: '#dde4e3'
  on-surface: '#161d1d'
  on-surface-variant: '#48464b'
  inverse-surface: '#2b3231'
  inverse-on-surface: '#ebf2f1'
  outline: '#79767c'
  outline-variant: '#c9c5cb'
  surface-tint: '#605d67'
  primary: '#212028'
  on-primary: '#ffffff'
  primary-container: '#37353e'
  on-primary-container: '#a19da8'
  inverse-primary: '#c9c4d0'
  secondary: '#5e5d68'
  on-secondary: '#ffffff'
  secondary-container: '#e3e1ee'
  on-secondary-container: '#64636e'
  tertiary: '#242115'
  on-tertiary: '#ffffff'
  tertiary-container: '#3a3629'
  on-tertiary-container: '#a59f8e'
  error: '#ba1a1a'
  on-error: '#ffffff'
  error-container: '#ffdad6'
  on-error-container: '#93000a'
  primary-fixed: '#e5e0ec'
  primary-fixed-dim: '#c9c4d0'
  on-primary-fixed: '#1c1a23'
  on-primary-fixed-variant: '#48454f'
  secondary-fixed: '#e3e1ee'
  secondary-fixed-dim: '#c7c5d1'
  on-secondary-fixed: '#1a1b24'
  on-secondary-fixed-variant: '#464650'
  tertiary-fixed: '#eae2cf'
  tertiary-fixed-dim: '#cdc6b4'
  on-tertiary-fixed: '#1f1b10'
  on-tertiary-fixed-variant: '#4b4739'
  background: '#f4fbfa'
  on-background: '#161d1d'
  surface-variant: '#dde4e3'
typography:
  display-lg:
    fontFamily: Merriweather
    fontSize: 48px
    fontWeight: '700'
    lineHeight: '1.2'
    letterSpacing: -0.02em
  headline-lg:
    fontFamily: Merriweather
    fontSize: 32px
    fontWeight: '700'
    lineHeight: '1.3'
  headline-md:
    fontFamily: Merriweather
    fontSize: 24px
    fontWeight: '700'
    lineHeight: '1.4'
  body-lg:
    fontFamily: Inter
    fontSize: 18px
    fontWeight: '400'
    lineHeight: '1.6'
  body-md:
    fontFamily: Inter
    fontSize: 16px
    fontWeight: '400'
    lineHeight: '1.6'
  label-md:
    fontFamily: Inter
    fontSize: 14px
    fontWeight: '600'
    lineHeight: '1.2'
    letterSpacing: 0.01em
  label-sm:
    fontFamily: Inter
    fontSize: 12px
    fontWeight: '500'
    lineHeight: '1.2'
  headline-lg-mobile:
    fontFamily: Merriweather
    fontSize: 28px
    fontWeight: '700'
    lineHeight: '1.3'
rounded:
  sm: 0.5rem
  DEFAULT: 1rem
  md: 1.5rem
  lg: 2rem
  xl: 3rem
  full: 9999px
spacing:
  unit: 8px
  container-padding: 32px
  gutter: 24px
  stack-gap: 16px
  section-margin: 64px
---

## Brand & Style

This design system employs a **Claymorphic** aesthetic tailored for a high-focus academic environment. The objective is to transform the typically rigid, flat nature of educational software into a tactile, approachable, and physically intuitive space. 

By leveraging "inflated" surfaces, the UI reduces visual fatigue and creates a sense of depth that guides the eye toward active learning modules. The personality is professional and grounded, avoiding the neon saturation of casual claymorphism in favor of a muted, sophisticated palette. The interaction model mimics physical clay: elements feel substantial, softly rounded, and responsive to pressure, evoking a sense of calm and focused productivity.

## Colors

The palette is anchored by the **Grayish-cyan (#D3DAD9)** canvas, which provides a soft, non-reflective base that minimizes eye strain during long study sessions. 

- **Primary (Charcoal):** Used for high-level information hierarchy, primary navigation, and text where maximum contrast is required.
- **Secondary (Deep Slate):** Utilized for structural UI elements, secondary buttons, and icons.
- **Accent (Mauve):** Reserved for highlights, progress indicators, and call-to-action details to provide a warm, intellectual contrast to the cool canvas.
- **Surface Rendering:** Claymorphic depth is achieved by using white and dark-tinted transparencies (inner shadows) rather than traditional flat color shifts.

## Typography

The typographic strategy balances academic tradition with modern utility. **Merriweather** provides an authoritative, literary feel for headings and intellectual content, suggesting a deep-seated respect for the written word. **Inter** handles the functional data-heavy aspects of the engine, ensuring that metadata, timers, and navigation remain legible at small sizes.

Large display type should maintain a slight negative letter spacing to feel "pressed" into the layout. Body text utilizes a generous line height (1.6) to accommodate the spacious, airy nature of claymorphic containers.

## Layout & Spacing

The layout follows a **Fluid-Grid** model with significant negative space to allow the "inflated" component shadows enough room to breathe without overlapping awkwardly. 

- **Desktop:** 12-column grid with 24px gutters and wide 64px side margins.
- **Tablet:** 8-column grid with 20px gutters and 32px margins.
- **Mobile:** 4-column grid with 16px gutters and 16px margins.

Vertical rhythm is strictly maintained in increments of 8px. Components are grouped into "Study Blocks" with 32px of internal padding to reinforce the pillowy, spacious feel of the design system.

## Elevation & Depth

Depth is the primary communicator of hierarchy in this design system. We use a triple-layer shadow technique to simulate the 3D clay effect:

1.  **Outer Shadow (Diffused):** A large, soft drop shadow (Color: #A8B2B1, Blur: 30px-50px) that lifts the element from the canvas.
2.  **Inner Shadow (Highlight):** A white semi-transparent inner shadow (Top-Left) to simulate light hitting the "top" of the inflated surface.
3.  **Inner Shadow (Depth):** A dark-tinted semi-transparent inner shadow (Bottom-Right) to simulate the curve of the element back toward the canvas.

Elements with higher priority receive larger outer blurs and more pronounced inner highlights. Hover states should "deflate" the element slightly by reducing the outer shadow distance and increasing inner shadow intensity.

## Shapes

The shape language is defined by extreme roundedness. Every corner must be soft to maintain the clay metaphor. 

- **Base Cards:** 24px to 32px corner radius.
- **Buttons & Inputs:** Fully pill-shaped (rounded-full).
- **Icons:** Use a 2px stroke weight with rounded caps and joins to match the soft-edge aesthetic.

Avoid sharp 90-degree angles entirely; even the most structural layout containers should have a minimum of 16px corner radius.

## Components

### Buttons
Buttons must feel tactile and pressable. They utilize a primary color fill (#37353E) with a subtle inner white glow on the top edge. On `:active` states, the button should shift downwards by 2px and the outer shadow should decrease, simulating a physical press into the clay.

### Cards
Cards are the primary content vessel. They use the canvas color (#D3DAD9) or white (#FFFFFF) as a base, differentiated only by their claymorphic shadows. They should have generous internal padding (32px) and no visible borders.

### Input Fields
Inputs are recessed. Unlike cards, inputs should look like they are "pushed into" the clay. Use an inner shadow (inset) on the top and left to create a concave effect. Use Inter (16px) for input text.

### Study Chips
Small, pill-shaped indicators for tags or categories. These should have a very subtle clay effect to avoid visual clutter. Use the Accent color (#715A5A) for active chips with white text.

### Progress Gauges
Utilize thick, rounded strokes for progress bars. The background of the bar should be recessed (inset shadow), and the active progress fill should be an inflated "slug" that sits on top of the track.