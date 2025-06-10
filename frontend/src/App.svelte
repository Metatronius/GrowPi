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
  let phCal = {};
  let phCalMsg = '';
  let phCalPoints = [];
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
    // Fetch calibration points for progress
    const configRes = await fetch('/get');
    const configData = await configRes.json();
    phCalPoints = configData["PH Calibration Points"] || [];
    config["PH Calibration Points"] = phCalPoints;
  }

  // Add calibration point with a known pH value
  async function addPhCalPoint(known_ph) {
    const res = await fetch('/ph_calibration_point', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ known_ph })
    });
    const result = await res.json();
    phCalMsg = result.message || result.error;
    await fetchPhCal();
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

  let newPlugType = "Fan";
  let newPlugIP = "";

  const plugTypes = ["Fan", "Humidifier", "Light", "Dehumidifier", "Heater"];

  function addPlug() {
    if (newPlugType && newPlugIP) {
      config["Kasa configs"].Device_IPs[newPlugType] = newPlugIP;
      newPlugIP = "";
      setKasa();
    }
  }

  function removePlug(name) {
    delete config["Kasa configs"].Device_IPs[name];
    setKasa();
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
  $: hum = currentStage && (
    config.Units["Humidity Metric"] === "VPD"
      ? config["Ideal Ranges"][currentStage]?.["VPD"]
      : config["Ideal Ranges"][currentStage]?.["Relative Humidity"]
  );
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

  // Save units and display settings to backend
  async function saveUnits() {
    await fetch('/set_units', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(config.Units)
    });
    alert('Units and display settings updated!');
    await fetchConfig();
    await getStatus();
  }
</script>

<h1 style="text-align:center; margin-top:1em; margin-bottom:0.5em;">GrowPi Dashboard</h1>
<nav>
  <button on:click={() => menu = 'status'}>Status</button>
  <button on:click={() => menu = 'ranges'}>Ideal Ranges</button>
  <button on:click={() => menu = 'kasa'}>Kasa Config</button>
  <button on:click={() => menu = 'light'}>Light Schedule</button>
  <button on:click={() => menu = 'phcal'}>pH Calibration</button>
  <button on:click={() => menu = 'email'}>Email Settings</button>
  <button on:click={() => menu = 'units'}>Units</button> 
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
          {status.temperature !== undefined ? Number(status.temperature).toFixed(2) : ''}°{config.Units.Temperature}
        </span>
        <small>
          Target: {lights.target}°{config.Units.Temperature}
          (Range: {lights.min}–{lights.max}°{config.Units.Temperature})
        </small>
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
        <strong>{config.Units["Humidity Metric"] === "VPD" ? "VPD" : "Humidity"}:</strong>
        <span>
          {status.humidity !== undefined ? status.humidity.toFixed(2) : ''}
          {config.Units["Humidity Metric"] === "VPD" ? " kPa" : "%"}
        </span>
        <small>
          Target: {hum.target}{config.Units["Humidity Metric"] === "VPD" ? " kPa" : "%"}
          (Range: {hum.min}–{hum.max}{config.Units["Humidity Metric"] === "VPD" ? " kPa" : "%"})
        </small>
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
          {status.wtemp !== undefined ? status.wtemp.toFixed(2) : ''}°{config.Units.Temperature}
        </span>
        <small>
          Target: {wtemp.target}°{config.Units.Temperature}
          (Range: {wtemp.min}–{wtemp.max}°{config.Units.Temperature})
        </small>
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
          {status.ph !== undefined ? Number(status.ph).toFixed(2) : ''}
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
  <label>
    Username:
    <input type="text" bind:value={config["Kasa configs"].Username} />
  </label>
  <label>
    Password:
    <input type="password" bind:value={config["Kasa configs"].Password} />
  </label>

  <h3>Device IPs</h3>
  <ul>
    {#each Object.entries(config["Kasa configs"].Device_IPs) as [name, ip]}
      <li>
        <strong>{name}:</strong>
        <input type="text" bind:value={config["Kasa configs"].Device_IPs[name]} />
        <button on:click={() => removePlug(name)}>Remove</button>
      </li>
    {/each}
  </ul>

  {#if plugTypes.filter(type => !(type in config["Kasa configs"].Device_IPs)).length > 0}
    <div style="margin-top:1em;">
      <select bind:value={newPlugType}>
        {#each plugTypes.filter(type => !(type in config["Kasa configs"].Device_IPs)) as type}
          <option value={type}>{type}</option>
        {/each}
      </select>
      <input placeholder="Plug IP" bind:value={newPlugIP} />
      <button on:click={addPlug} disabled={!newPlugType || !newPlugIP}>Add Plug</button>
    </div>
  {/if}

  <button on:click={setKasa}>Save Kasa Config</button>
{/if}

{#if menu === 'light'}
  <h2>Light Schedule</h2>
  <div style="margin-bottom:1em;">
    <strong>Current Schedule:</strong>
    On: {status.light_on} &nbsp; Off: {status.light_off}
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
  <p>
    Step 1: Place the probe in a calibration solution and click the corresponding button.<br>
    <small>For best results, use 7.00 and 4.00 for 2-point, or add 10.00 for 3-point calibration.</small>
  </p>
  <div style="display: flex; gap: 1em; margin-bottom: 1em;">
    <button on:click={() => addPhCalPoint(7.0)}>Add 7.00</button>
    <button on:click={() => addPhCalPoint(4.0)}>Add 4.00</button>
    <button on:click={() => addPhCalPoint(10.0)}>Add 10.00</button>
  </div>
  <div>
    <strong>Calibration Progress:</strong>
    {#if phCal && phCal.type}
      <span style="color: green;">
        {phCal.type === 'linear' ? '2-point calibration complete' : '3-point calibration complete'}
      </span>
    {:else if config["PH Calibration Points"] && config["PH Calibration Points"].length > 0}
      <span>
        {config["PH Calibration Points"].length} point(s) added.
        {config["PH Calibration Points"].length === 1 ? 'Add one more for 2-point calibration.' : ''}
        {config["PH Calibration Points"].length === 2 ? 'Add one more for 3-point calibration (optional).' : ''}
      </span>
    {:else}
      <span>No calibration points added yet.</span>
    {/if}
  </div>
  {#if phCalMsg}
    <div style="color: green; margin-top: 1em;">{phCalMsg}</div>
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

{#if menu === 'units'}
  <h2>Units & Display Settings</h2>
  <form on:submit|preventDefault={saveUnits}>
    <label>
      Temperature Unit:
      <select bind:value={config.Units.Temperature}>
        <option value="F">Fahrenheit (°F)</option>
        <option value="C">Celsius (°C)</option>
      </select>
    </label>
    <label>
      Time Format:
      <select bind:value={config.Units.Time}>
        <option value="12h">12-hour (AM/PM)</option>
        <option value="24h">24-hour</option>
      </select>
    </label>
    <label>
      Humidity Metric:
      <select bind:value={config.Units["Humidity Metric"]}>
        <option value="RH">Relative Humidity (%)</option>
        <option value="VPD">Vapor Pressure Deficit (kPa)</option>
      </select>
    </label>
    <button type="submit">Save</button>
  </form>
{/if}