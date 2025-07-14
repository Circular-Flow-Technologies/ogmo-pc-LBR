<script>
  export let value = 200; // Range: 0–100
  export let label = "Value";
  export let maxValue = 100;

  // Original range was -144° to +144°
  // Rotated -90°: new range is -234° to +54°
  const startAngle = -234;
  const endAngle = 54;

  // Convert value to angle
  $: angleDeg = startAngle + (value / maxValue) * (endAngle - startAngle);
  $: angleRad = (angleDeg * Math.PI) / 180;

  const radius = 80;
  $: needleX = 100 + radius * Math.cos(angleRad);
  $: needleY = 100 + radius * Math.sin(angleRad);

  function describeArc(start, end, r) {
    const startRad = (start * Math.PI) / 180;
    const endRad = (end * Math.PI) / 180;
    const largeArcFlag = end - start <= 180 ? 0 : 1;

    const x1 = 100 + r * Math.cos(startRad);
    const y1 = 100 + r * Math.sin(startRad);
    const x2 = 100 + r * Math.cos(endRad);
    const y2 = 100 + r * Math.sin(endRad);

    return `M ${x1} ${y1} A ${r} ${r} 0 ${largeArcFlag} 1 ${x2} ${y2}`;
  }

  $: backgroundArc = describeArc(startAngle, endAngle, radius);
  $: valueArc = describeArc(startAngle, angleDeg, radius);
</script>

<div class="w-52 h-52 relative text-pink-800">
  <svg viewBox="0 0 200 200" class="w-full h-full">
    <!-- Background arc -->
    <path
      d={backgroundArc}
      class="stroke-gray-200"
      stroke-width="16"
      fill="none"
    />

    <!-- Foreground arc -->
    <path
      d={valueArc}
      stroke="currentColor"
      stroke-width="16"
      fill="none"
      stroke-linecap="round"
    />

    <!-- Needle
    <line
      x1="100"
      y1="100"
      x2={needleX}
      y2={needleY}
      stroke="currentColor"
      stroke-width="3"
    />

    <circle cx="100" cy="100" r="4" fill="currentColor" /> -->
  </svg>

  <div
    class="absolute top-1/2 left-1/2 transform -translate-x-1/2 -translate-y-1/2 text-center"
  >
    <div class="text-sm text-gray-500">{label}</div>
    <div class="text-2xl font-bold text-gray-800">{value}%</div>
  </div>
</div>
