<script>
  export let phCal;
  export let phCalMsg;
  export let savePhCal;
  export let addPhCalPoint;
</script>

<h2>pH Probe Calibration</h2>
<p>Step 1: Place the probe in a known pH solution (e.g., 4.00, 7.00, or 10.00).</p>
<input type="number" step="any" bind:value={phCal.known_ph} placeholder="Known pH value" />
<button on:click={addPhCalPoint}>Add Calibration Point</button>

{#if phCalMsg}
  <div style="color: green;">{phCalMsg}</div>
{/if}

<!-- Optionally, show current calibration values -->
{#if phCal.slope !== undefined && phCal.intercept !== undefined}
  <div style="margin-top:1em;">
    <strong>Current Slope:</strong> {phCal.slope}<br>
    <strong>Current Intercept:</strong> {phCal.intercept}
  </div>
{/if}

<button style="margin-top:1em;" on:click={savePhCal}>Save Calibration</button>