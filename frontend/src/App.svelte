<script>
  import { onMount } from 'svelte';

  let status = {};
  let config = {
    "Sensor Pins": {},
    "Ideal Ranges": {},
    "Kasa configs": { Username: "", Password: "", Device_IPs: {} }
  };
  let menu = 'status';
  let selectedStage = '';
  let stageToSet = '';
  let findingKasa = false;
  let kasaError = '';
  let discoveredIPs = {};
  let lightOn = '';
  let lightOff = '';
  let currentLightOn = '';
  let currentLightOff = '';
  let phCal = { known_ph: '' };
  let phCalMsg = '';
  let emailSettings = {
    smtp_server: "",
    smtp_port: 587,
    username: "",
    password: "",
    from_email: "",
    to_email: ""
  };

  const stageOrder = ["Seedling", "Vegetative", "Flowering", "Drying"];

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
      body: JSON.stringify({ stage: stageToSet })
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

  // Fetch the light schedule from the backend
  async function fetchLightSchedule() {
    const res = await fetch('/light_schedule');
    const sched = await res.json();
    currentLightOn = sched.on || "06:00";
    currentLightOff = sched.off || "22:00";
    lightOn = currentLightOn;
    lightOff = currentLightOff;
  }

  // Save the light schedule to the backend
  async function saveLightSchedule() {
    await fetch('/light_schedule', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ on: lightOn, off: lightOff })
    });
    alert('Light schedule updated!');
    fetchLightSchedule();
  }

  async function fetchPhCal() {
    const res = await fetch('/ph_calibration');
    phCal = await res.json();
  }

  async function savePhCal() {
    const res = await fetch('/ph_calibration', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(phCal)
    });
    const result = await res.json();
    phCalMsg = result.message || result.error;
    fetchPhCal();
  }

  async function addPhCalPoint() {
    const res = await fetch('/ph_calibration_point', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ known_ph: parseFloat(phCal.known_ph) })
    });
    const result = await res.json();
    phCalMsg = result.message || result.error;
    phCal.known_ph = '';
    fetchPhCal();
  }

  async function fetchEmailSettings() {
    const res = await fetch('/email_settings');
    emailSettings = await res.json();
  }

  async function saveEmailSettings() {
    await fetch('/email_settings', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(emailSettings)
    });
    alert('Email settings updated!');
  }

  // Fetch data on mount
  onMount(() => {
    fetchConfig();
    getStatus();
    fetchLightSchedule();
    fetchPhCal();
    fetchEmailSettings();
  });

  // Default selectedStage to current stage when switching to ranges tab
  $: if (menu === 'ranges' && config["State"]?.["Current Stage"]) {
    selectedStage = config["State"]["Current Stage"];
  }
  // Always fetch light schedule when switching to light tab
  $: if (menu === 'light') {
    fetchLightSchedule();
  }
  $: if (!selectedStage && Object.keys(config["Ideal Ranges"]).length > 0) {
    selectedStage = Object.keys(config["Ideal Ranges"])[0];
  }
  $: if (!stageToSet && config["State"]?.["Current Stage"]) {
    stageToSet = config["State"]["Current Stage"];
  }
  $: if (menu === 'phcal') {
    fetchPhCal();
  }

  // Computed values for current stage and ranges
  $: currentStage = config["State"]?.["Current Stage"];
  $: air = currentStage && config["Ideal Ranges"][currentStage]?.["Air Temperature"];
  $: lights = air && (air["Lights On"] || air["Lights Off"] || air);
  $: hum = currentStage && config["Ideal Ranges"][currentStage]?.["Relative Humidity"];
  $: wtemp = currentStage && config["Ideal Ranges"][currentStage]?.["Water Temperature"];
  $: ph = currentStage && config["Ideal Ranges"][currentStage]?.["Water pH"];

  function statusColor(on) {
    return on ? 'green' : 'red';
  }

  function readingColor(val, target, min, max) {
    if (val === undefined || target === undefined || min === undefined || max === undefined) return 'gray';
    if (Math.abs(val - target) <= 1.0) return 'green';
    if (val >= min && val <= max) return 'goldenrod';
    return 'red';
  }

  function sliderPercent(val, min, max) {
    if (val === undefined || min === undefined || max === undefined) return 0;
    return Math.max(0, Math.min(100, ((val - min) / (max - min)) * 100));
  }

  function to12Hour(timeStr) {
    if (!timeStr) return '';
    const [hour, minute] = timeStr.split(':').map(Number);
    const ampm = hour >= 12 ? 'PM' : 'AM';
    const hour12 = ((hour + 11) % 12 + 1);
    return `${hour12}:${minute.toString().padStart(2, '0')} ${ampm}`;
  }
</script>

<h1 style="text-align:center; margin-top:1em; margin-bottom:0.5em;">GrowPi Dashboard</h1>
<nav>
  <button on:click={() => menu = 'status'}>Status</button>
  <button on:click={() => menu = 'ranges'}>Ideal Ranges</button>
  <button on:click={() => menu = 'kasa'}>Kasa Config</button>
  <button on:click={() => menu = 'light'}>Light Schedule</button>
  <button on:click={() => menu = 'phcal'}>pH Calibration</button>
  <button on:click={() => menu = 'email'}>Email Settings</button> <!-- Add this line -->
</nav>
<div style="margin-bottom: 2em;"></div>

{#if menu === 'status'}
  {#if config["State"]?.["Current Stage"]}
    <!-- Air Temperature -->
    {#if lights}
      <div style="display:flex; flex-direction:column; align-items:center; margin-bottom:1em;">
        <div style="height:24px; background:#eee; border-radius:12px; width:200px; position:relative;">
          <div style="
            position:absolute;
            left:0;
            top:8px;
            height:8px;
            width:100%;
            background:linear-gradient(
              to right,
              red 0%,
              goldenrod 20%,
              green 40%,
              green 60%,
              goldenrod 80%,
              red 100%
            );
            border-radius:4px;">
          </div>
          {#if status.temperature !== undefined && lights.min !== undefined && lights.max !== undefined}
            <div style="
              position:absolute;
              top:2px;
              left:calc({sliderPercent(status.temperature, lights.min, lights.max)}% - 8px);
              width:16px;
              height:16px;
              background:{readingColor(status.temperature, lights.target, lights.min, lights.max)};
              border:2px solid #333;
              border-radius:50%;
              transition:left 0.3s;">
            </div>
          {/if}
        </div>
        <strong>Air Temperature:</strong>
        <span style="color: {readingColor(status.temperature, lights.target, lights.min, lights.max)}">
          {status.temperature !== undefined ? status.temperature.toFixed(2) : ''}°F
        </span>
        <small>Target: {lights.target}°F (Range: {lights.min}–{lights.max})</small>
      </div>
    {/if}

    <!-- Humidity -->
    {#if hum}
      <div style="display:flex; flex-direction:column; align-items:center; margin-bottom:1em;">
        <div style="height:24px; background:#eee; border-radius:12px; width:200px; position:relative;">
          <div style="
            position:absolute;
            left:0;
            top:8px;
            height:8px;
            width:100%;
            background:linear-gradient(
              to right,
              red 0%,
              goldenrod 20%,
              green 40%,
              green 60%,
              goldenrod 80%,
              red 100%
            );
            border-radius:4px;">
          </div>
          {#if status.humidity !== undefined && hum.min !== undefined && hum.max !== undefined}
            <div style="
              position:absolute;
              top:2px;
              left:calc({sliderPercent(status.humidity, hum.min, hum.max)}% - 8px);
              width:16px;
              height:16px;
              background:{readingColor(status.humidity, hum.target, hum.min, hum.max)};
              border:2px solid #333;
              border-radius:50%;
              transition:left 0.3s;">
            </div>
          {/if}
        </div>
        <strong>Humidity:</strong>
        <span style="color: {readingColor(status.humidity, hum.target, hum.min, hum.max)}">
          {status.humidity !== undefined ? status.humidity.toFixed(2) : ''}%
        </span>
        <small>Target: {hum.target}% (Range: {hum.min}–{hum.max})</small>
      </div>
    {/if}

    <!-- Water Temperature -->
    {#if wtemp}
      <div style="display:flex; flex-direction:column; align-items:center; margin-bottom:1em;">
        <div style="height:24px; background:#eee; border-radius:12px; width:200px; position:relative;">
          <div style="
            position:absolute;
            left:0;
            top:8px;
            height:8px;
            width:100%;
            background:linear-gradient(
              to right,
              red 0%,
              goldenrod 20%,
              green 40%,
              green 60%,
              goldenrod 80%,
              red 100%
            );
            border-radius:4px;">
          </div>
          {#if status.wtemp !== undefined && wtemp.min !== undefined && wtemp.max !== undefined}
            <div style="
              position:absolute;
              top:2px;
              left:calc({sliderPercent(status.wtemp, wtemp.min, wtemp.max)}% - 8px);
              width:16px;
              height:16px;
              background:{readingColor(status.wtemp, wtemp.target, wtemp.min, wtemp.max)};
              border:2px solid #333;
              border-radius:50%;
              transition:left 0.3s;">
            </div>
          {/if}
        </div>
        <strong>Water Temperature:</strong>
        <span style="color: {readingColor(status.wtemp, wtemp.target, wtemp.min, wtemp.max)}">
          {status.wtemp !== undefined ? status.wtemp.toFixed(2) : ''}°F
        </span>
        <small>Target: {wtemp.target}°F (Range: {wtemp.min}–{wtemp.max})</small>
      </div>
    {/if}

    <!-- Water pH -->
    {#if ph}
      <div style="display:flex; flex-direction:column; align-items:center; margin-bottom:1em;">
        <div style="height:24px; background:#eee; border-radius:12px; width:200px; position:relative;">
          <div style="
            position:absolute;
            left:0;
            top:8px;
            height:8px;
            width:100%;
            background:linear-gradient(
              to right,
              red 0%,
              goldenrod 20%,
              green 40%,
              green 60%,
              goldenrod 80%,
              red 100%
            );
            border-radius:4px;">
          </div>
          {#if status.ph !== undefined && ph.min !== undefined && ph.max !== undefined}
            <div style="
              position:absolute;
              top:2px;
              left:calc({sliderPercent(status.ph, ph.min, ph.max)}% - 8px);
              width:16px;
              height:16px;
              background:{readingColor(status.ph, ph.target, ph.min, ph.max)};
              border:2px solid #333;
              border-radius:50%;
              transition:left 0.3s;">
            </div>
          {/if}
        </div>
        <strong>Water pH:</strong>
        <span style="color: {readingColor(status.ph, ph.target, ph.min, ph.max)}">
          {status.ph !== undefined ? status.ph : ''}
        </span>
        <small>Target: {ph.target} (Range: {ph.min}–{ph.max})</small>
      </div>
    {/if}

    <div style="display: flex; flex-direction: column; align-items: center; gap: 0.5em; margin-bottom: 1em;">
      <div>
        <strong>Fan:</strong>
        <span style="
          display:inline-block;
          width:12px;
          height:12px;
          margin-right:6px;
          border-radius:50%;
          background:{status.fan_status ? 'green' : 'red'};
          border:1.5px solid #333;
          vertical-align:middle;
        "></span>
        <span style="color: {status.fan_status ? 'green' : 'red'}">{status.fan_status ? 'ON' : 'OFF'}</span>
      </div>
      <div>
        <strong>Humidifier:</strong>
        <span style="
          display:inline-block;
          width:12px;
          height:12px;
          margin-right:6px;
          border-radius:50%;
          background:{status.humidifier_status ? 'green' : 'red'};
          border:1.5px solid #333;
          vertical-align:middle;
        "></span>
        <span style="color: {status.humidifier_status ? 'green' : 'red'}">{status.humidifier_status ? 'ON' : 'OFF'}</span>
      </div>
      <div>
        <strong>Light:</strong>
        <span style="
          display:inline-block;
          width:12px;
          height:12px;
          margin-right:6px;
          border-radius:50%;
          background:{status.light_status ? 'green' : 'red'};
          border:1.5px solid #333;
          vertical-align:middle;
        "></span>
        <span style="color: {status.light_status ? 'green' : 'red'}">{status.light_status ? 'ON' : 'OFF'}</span>
      </div>
    </div>

    <button on:click={getStatus}>Refresh</button>

    <div style="display: flex; justify-content: center; margin-top: 2em;">
      <fieldset style="padding:1em; border:2px solid #4CAF50; border-radius:8px; max-width:350px;">
        <legend style="font-weight:bold; color:#4CAF50;">Change Grow Stage</legend>
        <label style="margin-right:1em;">
          <span style="margin-right:0.5em;">Select Stage:</span>
          <select bind:value={stageToSet} style="padding:0.3em;">
            {#each stageOrder.filter(stage => config["Ideal Ranges"][stage]) as stage}
              <option value={stage}>{stage}</option>
            {/each}
          </select>
        </label>
        <button on:click={setStage} style="margin-left:1em; padding:0.4em 1em; background:#4CAF50; color:white; border:none; border-radius:4px;">
          Set Stage
        </button>
      </fieldset>
    </div>
  {/if}
{/if}

{#if menu === 'ranges'}
  <select bind:value={selectedStage}>
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
  {/if}
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

{#if menu === 'light'}
  <h2>Light Schedule</h2>
  <div style="margin-bottom:1em;">
    <strong>Current Schedule:</strong>
    On: {to12Hour(currentLightOn)} &nbsp; Off: {to12Hour(currentLightOff)}
  </div>
  <form on:submit|preventDefault={saveLightSchedule}>
    <label>
      On Time:
      <input type="time" bind:value={lightOn} required />
    </label>
    <label>
      Off Time:
      <input type="time" bind:value={lightOff} required />
    </label>
    <button type="submit">Save Schedule</button>
  </form>
{/if}

{#if menu === 'phcal'}
  <h2>pH Probe Calibration</h2>
  <p>Step 1: Place the probe in a known pH solution (e.g., 4.00, 7.00, or 10.00).</p>
  <input type="number" step="any" bind:value={phCal.known_ph} placeholder="Known pH value" />
  <button on:click={addPhCalPoint}>Add Calibration Point</button>
  {#if phCalMsg}
    <div style="color: green;">{phCalMsg}</div>
  {/if}
{/if}

{#if menu === 'email'}
  <h2>Email Settings</h2>
  <form on:submit|preventDefault={saveEmailSettings}>
    <label>SMTP Server: <input type="text" bind:value={emailSettings.smtp_server} /></label>
    <label>SMTP Port: <input type="number" bind:value={emailSettings.smtp_port} /></label>
    <label>Username: <input type="text" bind:value={emailSettings.username} /></label>
    <label>Password: <input type="password" bind:value={emailSettings.password} /></label>
    <label>From Email: <input type="email" bind:value={emailSettings.from_email} /></label>
    <label>To Email: <input type="email" bind:value={emailSettings.to_email} /></label>
    <button type="submit">Save</button>
  </form>
{/if}