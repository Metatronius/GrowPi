<script>
  export let config;
  export let setKasa;
  export let findKasaDevices;
  export let findingKasa;
  export let kasaError;
  export let discoveredIPs;
</script>

<h2>Kasa Configuration</h2>
<label>
  Username:
  <input type="text" bind:value={config["Kasa configs"].Username} />
</label>
<label>
  Password:
  <input type="password" bind:value={config["Kasa configs"].Password} />
</label>
<h3>Device IPs</h3>
{#each Object.entries(config["Kasa configs"].Device_IPs) as [key, value]}
  <label>
    {key}:
    <input type="text" bind:value={config["Kasa configs"].Device_IPs[key]} />
  </label>
{/each}
<button on:click={setKasa}>Set Kasa Config</button>
<button on:click={findKasaDevices} disabled={findingKasa}>
  {findingKasa ? 'Finding...' : 'Find Kasa Devices'}
</button>
{#if kasaError}
  <div style="color: red;">{kasaError}</div>
{/if}
{#if Object.keys(discoveredIPs).length > 0}
  <h4>Discovered Devices:</h4>
  <ul>
    {#each Object.entries(discoveredIPs) as [name, ip]}
      <li>{name}: {ip}</li>
    {/each}
  </ul>
{/if}