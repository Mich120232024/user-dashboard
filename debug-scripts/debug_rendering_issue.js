// Debug script to identify why components aren't rendering below
console.log("🔍 DEBUGGING COMPONENT RENDERING ISSUE");

// 1. Check container dimensions
console.log("\n📏 Checking Container Dimensions:");
const containers = document.querySelectorAll('.tab-content, .dashboard-content, [role="tabpanel"]');
containers.forEach((container, index) => {
    const rect = container.getBoundingClientRect();
    const computed = getComputedStyle(container);
    console.log(`Container ${index + 1}:`, {
        class: container.className,
        height: rect.height,
        scrollHeight: container.scrollHeight,
        overflow: computed.overflow,
        position: computed.position,
        display: computed.display,
        visibility: computed.visibility
    });
    
    // Check if content is cut off
    if (container.scrollHeight > rect.height) {
        console.warn(`⚠️ Container ${index + 1} is cutting off content!`);
        console.log(`   Visible: ${rect.height}px, Total: ${container.scrollHeight}px`);
    }
});

// 2. Find hidden components
console.log("\n👻 Finding Hidden Components:");
const allComponents = document.querySelectorAll('.component, .widget, .chart, .fred-component, [data-component]');
let hiddenCount = 0;

allComponents.forEach((component, index) => {
    const rect = component.getBoundingClientRect();
    const computed = getComputedStyle(component);
    const isHidden = (
        rect.height === 0 ||
        computed.display === 'none' ||
        computed.visibility === 'hidden' ||
        computed.opacity === '0'
    );
    
    if (isHidden) {
        hiddenCount++;
        console.warn(`❌ Hidden Component ${index + 1}:`, {
            class: component.className,
            id: component.id,
            display: computed.display,
            visibility: computed.visibility,
            height: rect.height,
            parent: component.parentElement?.className
        });
    }
});

console.log(`\n📊 Total: ${allComponents.length} components, Hidden: ${hiddenCount}`);

// 3. Check parent constraints
console.log("\n🔒 Checking Parent Constraints:");
const problemParents = document.querySelectorAll('[style*="height"], [style*="overflow"]');
problemParents.forEach(parent => {
    const computed = getComputedStyle(parent);
    if (computed.overflow === 'hidden' || computed.height.includes('px')) {
        console.warn("⚠️ Constraining Parent:", {
            element: parent,
            class: parent.className,
            height: computed.height,
            overflow: computed.overflow,
            children: parent.children.length
        });
    }
});

// 4. Quick fix function
window.quickRenderFix = function() {
    console.log("\n🔧 Applying Quick Render Fix...");
    
    // Remove all height constraints
    document.querySelectorAll('*').forEach(el => {
        if (el.style.height && el.style.height !== 'auto') {
            el.style.height = 'auto';
        }
        if (el.style.overflow === 'hidden') {
            el.style.overflow = 'visible';
        }
    });
    
    // Force display all components
    document.querySelectorAll('.component, .widget').forEach(comp => {
        comp.style.display = 'block';
        comp.style.visibility = 'visible';
        comp.style.opacity = '1';
    });
    
    console.log("✅ Quick fix applied! Check if components appear now.");
};

// 5. Layout mode check
console.log("\n📐 Current Layout Mode:");
const layoutSelector = document.querySelector('select:has(option:contains("Saved Layout")), input[type="radio"][name*="layout"]');
if (layoutSelector) {
    console.log("Layout selector found:", layoutSelector.value || layoutSelector.checked);
} else {
    console.log("❌ No layout selector found");
}

console.log("\n💡 Run quickRenderFix() to force all components visible");
console.log("💡 This will help identify if it's a CSS issue");