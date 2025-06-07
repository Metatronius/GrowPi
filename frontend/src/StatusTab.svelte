<script>
  export let config;
  export let status;
  export let stageOrder;
  export let setStage;
  export let stageToSet;
  export let getStatus;
  export let currentStage;
  export let air;
  export let lights;
  export let hum;
  export let wtemp;
  export let ph;
  export let sliderPercent;
  export let readingColor;
  export let statusColor;
</script>

<h2>Status</h2>

{#if config["State"]}
  <div>
    <strong>Current Stage:</strong> {config["State"]["Current Stage"]}
    <select bind:value={stageToSet}>
      <option disabled value="">Change Stage</option>
      {#each stageOrder as stage}
        <option value={stage}>{stage}</option>
      {/each}
    </select>
    <button on:click={setStage} disabled={!stageToSet}>Set Stage</button>
  </div>
  <div style="margin-top:1em;">
    <strong>Air Temperature:</strong> {config["State"]["Air Temperature"]}°F<br>
    <strong>Relative Humidity:</strong> {config["State"]["Relative Humidity"]}%<br>
    <strong>Water Temperature:</strong> {config["State"]["Water Temperature"]}°F<br>
    <strong>Water pH:</strong> {config["State"]["Water pH"]}<br>
    <strong>Fan Status:</strong> {config["State"]["Fan Status"] ? 'On' : 'Off'}<br>
    <strong>Light Status:</strong> {config["State"]["Light Status"] ? 'On' : 'Off'}<br>
    <strong>Water Pump Status:</strong> {config["State"]["Water Pump Status"] ? 'On' : 'Off'}<br>
  </div>
  <button style="margin-top:1em;" on:click={getStatus}>Refresh Status</button>
{/if}