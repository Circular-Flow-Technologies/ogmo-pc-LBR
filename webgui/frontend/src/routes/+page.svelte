<script lang="ts">
  import type { PageProps } from "./$types";
  import "../app.css";

  import { resource } from "$lib/resource.svelte";
  import Gauge from "$lib/Gauge.svelte";
  const data = resource(() =>
    fetch(`/api/data`).then((response) => response.json())
  );

  async function triggerAction() {
    const response = await fetch("/api/action", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({ action: "do_something" }),
    });

    const result = await response.json();
    console.log("Server responded with:", result);
    alert(`Server says: ${result.status}`);
  }

  //   console.log("Data fetched:", data.value); // Debugging line to check data
</script>

<main class="min-h-screen bg-gray-100 flex items-center justify-center p-6">
  <div class="bg-red rounded-xl shadow-md p-6 max-w-sm w-full text-center">
    <h1 class="text-xl font-semibold text-gray-800 mb-4">Sensor Dashboard</h1>

    {#if data.loading}
      <p class="text-gray-500">Loading...</p>
    {:else}
      <div class="flex space-y-2">
        <Gauge value={data.value?.temperature ?? 0} label="Temperature" />
        <Gauge value={data.value?.humidity ?? 0} label="Humidity" />
      </div>
      <button
        class="px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700 transition"
        onclick={triggerAction}>Start</button
      >
    {/if}
  </div>
</main>
