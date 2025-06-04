<script>
  let status = {};
  let config = {
    "Sensor Pins": {},
    "Ideal Ranges": {},
    "Kasa configs": { Username: "", Password: "", Device_IPs: {} }
  };
  let menu = 'status';
  let selectedStage = '';
  let findingKasa = false;
  let kasaError = '';
  let discoveredIPs = {};

  // Fetch all config data on mount
  async function fetchConfig() {
    const res = await fetch('/get');
    config = await res.json();
  }

  async function getStatus() {
    const res = await fetch('/api/status');
    status = await res.json();
  }

  async function setRanges() {
    await fetch('/set', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        stage: selectedStage,
        ranges: config["Ideal Ranges"][selectedStage]
      })
    });
    alert('Ranges updated!');
    fetchConfig();
  }

  async function setPins() {
    await fetch('/set_Pins', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(config["Sensor Pins"])
    });
    alert('Pins updated!');
    fetchConfig();
  }

  async function setKasa() {
    await fetch('/set_Kasa', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(config["Kasa configs"])
    });
    alert('Kasa config updated!');
    fetchConfig();
  }

  async function setRange(stage, meter, subkey, values) {
    await fetch('/set', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ stage, meter, subkey, values })
    });
    alert('Range updated!');
    fetchConfig();
  }

  async function setStage() {
    await fetch('/set_stage', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ stage: config["State"]["Current Stage"] })
    });
    alert('Stage updated!');
    fetchConfig();
  }

  async function findKasaDevices() {
    findingKasa = true;
    kasaError = '';
    discoveredIPs = {};
    try {
      const res = await fetch('/find_kasa');
      if (!res.ok) throw new Error('Failed to find Kasa devices');
      discoveredIPs = await res.json();
    } catch (e) {
      kasaError = e.message;
    }
    findingKasa = false;
  }

  fetchConfig();
  getStatus();

  $: if (!selectedStage && Object.keys(config["Ideal Ranges"]).length > 0) {
    selectedStage = Object.keys(config["Ideal Ranges"])[0];
  }
</script>

<nav>
  <button on:click={() => menu = 'status'}>Status</button>
  <button on:click={() => menu = 'ranges'}>Ideal Ranges</button>
  <button on:click={() => menu = 'pins'}>Sensor Pins</button>
  <button on:click={() => menu = 'kasa'}>Kasa Config</button>
</nav>

<main>
  {#if menu === 'status'}
    <h1>GrowPi Status</h1>
    <p><strong>Current Stage:</strong> {config["State"]?.["Current Stage"]}</p>
    <p>Air Temperature: {status.temperature}°F</p>
    <p>Humidity: {status.humidity}%</p>
    <p>PH: {status.ph}</p>
    <p>Water Temperature: {status.wtemp}</p>
    <button on:click={getStatus}>Refresh</button>

    <fieldset style="margin-top:2em; padding:1em; border:2px solid #4CAF50; border-radius:8px; max-width:350px;">
      <legend style="font-weight:bold; color:#4CAF50;">Change Grow Stage</legend>
      <label style="margin-right:1em;">
        <span style="margin-right:0.5em;">Select Stage:</span>
        <select bind:value={config["State"]["Current Stage"]} style="padding:0.3em;">
          {#each Object.keys(config["Ideal Ranges"]) as stage}
            <option value={stage}>{stage}</option>
          {/each}
        </select>
      </label>
      <button on:click={setStage} style="margin-left:1em; padding:0.4em 1em; background:#4CAF50; color:white; border:none; border-radius:4px;">
        Set Stage
      </button>
    </fieldset>
  {/if}

  {#if menu === 'ranges'}
    <h2>Set Ideal Ranges</h2>
    <label>
      Stage:
      <select bind:value={selectedStage}>
        {#each Object.keys(config["Ideal Ranges"]) as stage}
          <option value={stage}>{stage}</option>
        {/each}
      </select>
    </label>
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
    {/if}
  {/if}

  {#if menu === 'pins'}
    <h2>Set Sensor Pins</h2>
    {#each Object.entries(config["Sensor Pins"]) as [key, value]}
      <label>{key}: <input type="number" bind:value={config["Sensor Pins"][key]} min="0" max="7" /></label>
    {/each}
    <button on:click={setPins}>Set Pins</button>
  {/if}

  {#if menu === 'kasa'}
    <h2>Kasa Configuration</h2>
    <label>Username: <input type="text" bind:value={config["Kasa configs"].Username} /></label>
    <label>Password: <input type="password" bind:value={config["Kasa configs"].Password} /></label>
    <h3>Device IPs</h3>
    {#each Object.entries(config["Kasa configs"].Device_IPs) as [key, value]}
      <label>{key}: <input type="text" bind:value={config["Kasa configs"].Device_IPs[key]} /></label>
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
  {/if}
</main>
