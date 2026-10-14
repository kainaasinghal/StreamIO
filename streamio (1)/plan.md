# Streamio PDF-aligned admin dashboard plan

## Scope
Restore the Dashboard to the original cinematic streaming homepage with hero artwork, orbital graphics, search, genre filters, watchlist, play preview, and content rails. Redesign the remaining requested admin views—Users, Content, Watch History, Subscription, Payment History, and Reviews—using the attached Book2Oct2026.pdf as the primary visual reference.

## Visual direction
The secondary pages follow the PDF's StreamDB-inspired interface: deep midnight canvas, purple and burgundy ambient gradients, glass panels with restrained borders, luminous lime status accents, compact mono labels, strong white editorial headings, and content arranged as dense but breathable operations screens. Existing data/filter/modal interactions are preserved. Added motion includes staggered page entrance, ambient floating color fields, live-database pulse, lime progress sweeps, animated chart bars, poster scan highlights, hover lift, table row glow, and reduced-motion-friendly transitions.

## Page treatment
Users keeps its complete directory, filters, pagination, add/edit/deactivate workflow, and now gains the PDF's live database badge, stronger glass-table hierarchy, and lime activity accents. Content keeps poster management, filters, add/edit and preview workflows while adding cinematic poster sweeps. Subscription keeps plan analytics and comparison cards with the PDF's operational color language. Payment History keeps transaction search, filters, details, export, and refund interactions. Watch History keeps viewing analytics, device mix, detailed sessions, completion bars, and export feedback. Reviews keeps sentiment analytics, rating distribution, top titles, searchable feedback table, review details, export, and reply interaction.

## Structure
`src/main.jsx` keeps the existing cinematic Dashboard shell and navigation, while `src/styles.css` retains the existing responsive visual system. The visible management pages use `src/DatabasePages.jsx` and the shared `src/api.js` client to read and mutate MySQL-backed records through FastAPI. Dashboard metrics are calculated from the supplied normalized dataset; fields absent from the schema are not represented as live data.
