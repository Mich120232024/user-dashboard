// Quick debugging script for dropdown cursor issues
// Run this in browser console

console.log("🔍 DROPDOWN CURSOR DEBUG STARTED");

// 1. Find all dropdowns/selects
const dropdowns = document.querySelectorAll('select, .dropdown, [role="listbox"]');
console.log(`Found ${dropdowns.length} dropdown elements:`, dropdowns);

// 2. Check for problematic event listeners
dropdowns.forEach((dropdown, index) => {
    console.log(`\n📋 Dropdown ${index + 1}:`);
    console.log('Element:', dropdown);
    console.log('Style cursor:', getComputedStyle(dropdown).cursor);
    console.log('Position:', getComputedStyle(dropdown).position);
    console.log('Z-index:', getComputedStyle(dropdown).zIndex);
    
    // Check for event listeners (if element has them)
    const events = ['click', 'mousedown', 'mouseup', 'mousemove'];
    events.forEach(event => {
        // Create test listener to see if events are firing
        dropdown.addEventListener(event, (e) => {
            console.log(`🎯 ${event} fired on dropdown ${index + 1}`);
        }, { once: true });
    });
});

// 3. Check for global mouse event issues
let mouseEventCount = 0;
document.addEventListener('mousemove', (e) => {
    mouseEventCount++;
    if (mouseEventCount % 50 === 0) { // Log every 50th event to avoid spam
        console.log(`📍 Global mousemove events: ${mouseEventCount}`);
    }
});

// 4. Temporary fix - add CSS to prevent cursor sticking
const fixCSS = `
/* Temporary dropdown cursor fix */
select, .dropdown, [role="listbox"] {
    cursor: pointer !important;
    pointer-events: auto !important;
}

select:focus, .dropdown:focus, [role="listbox"]:focus {
    cursor: pointer !important;
}

/* Prevent component dragging */
.dropdown-container, .fred-component {
    pointer-events: none !important;
}

.dropdown-container select, .fred-component select {
    pointer-events: auto !important;
}
`;

// Apply temporary fix
const style = document.createElement('style');
style.textContent = fixCSS;
document.head.appendChild(style);

console.log("✅ Temporary CSS fix applied");
console.log("🔧 Try interacting with dropdowns now");

// 5. Monitor for cursor stuck events
let lastCursorChange = Date.now();
document.addEventListener('mousemove', () => {
    lastCursorChange = Date.now();
});

setInterval(() => {
    const timeSinceLastMove = Date.now() - lastCursorChange;
    if (timeSinceLastMove > 2000) { // If cursor hasn't moved for 2 seconds
        console.log("⚠️ Possible cursor stuck - no movement detected");
    }
}, 3000);

console.log("🔍 DROPDOWN CURSOR DEBUG COMPLETE - Monitor console for issues");