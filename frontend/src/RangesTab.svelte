<script>
  export let config;
  export let selectedStage;
  export let setRange;
  export let setRanges;
  export let stageOrder;
</script>

<h2>Ideal Ranges</h2>

<select bind:value={selectedStage}>
  <option disabled value="">Select Stage</option>
  {#each stageOrder.filter(stage => config["Ideal Ranges"][stage]) as stage}
    <option value={stage}>{stage}</option>
  {/each}
</select>

{#if selectedStage}
  {#each Object.entries(config["Ideal Ranges"][selectedStage]) as [meter, value]}
    <fieldset>
      <legend>{meter}</legend>
      {#if typeof value === 'object' && value["Lights On"]}
        <!-- Nested: Air Temperature -->
        {#each Object.entries(value) as [subkey, subval]}
          <fieldset>
            <legend>{subkey}</legend>
            <label>Min: <input type="number" bind:value={subval.min} step="any" /></label>
            <label>Max: <input type="number" bind:value={subval.max} step="any" /></label>
            <label>Target: <input type="number" bind:value={subval.target} step="any" /></label>
            <button on:click={() => setRange(selectedStage, meter, subkey, subval)}>Set</button>
          </fieldset>
        {/each}
      {:else}
        <!-- Flat: Relative Humidity, Water Temperature, Water pH -->
        <label>Min: <input type="number" bind:value={value.min} step="any" /></label>
        <label>Max: <input type="number" bind:value={value.max} step="any" /></label>
        <label>Target: <input type="number" bind:value={value.target} step="any" /></label>
        <button on:click={() => setRange(selectedStage, meter, null, value)}>Set</button>
      {/if}
    </fieldset>
  {/each}
  <button style="margin-top:1em;" on:click={setRanges}>Set All Ranges for {selectedStage}</button>
{/if}