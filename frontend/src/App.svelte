<script>
  let status = {};
  let idealRanges = {
    "Air Temperature": { min: 68, max: 72, target: 70 },
    "Relative Humidity": { min: 40, max: 60, target: 50 },
    "Water Temperature": { min: 70, max: 75, target: 72.5 },
    "Water pH": { min: 5.0, max: 6.0, target: 5.5 }
  };
  let pins = {
    TemperatureSensor: 0,
    RHMeter: 1,
    WaterTemperatureSensor: 2,
    PHMeter: 3
  };

  async function getStatus() {
    const res = await fetch('/api/status');
    status = await res.json();
  }

  async function setRanges() {
    await fetch('/set', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(idealRanges)
    });
    alert('Ranges updated!');
  }

  async function setPins() {
    await fetch('/set_Pins', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(pins)
    });
    alert('Pins updated!');
  }

  getStatus();
</script>

<main>
  <h1>GrowPi Status</h1>
  <p>Air Temperature: {status.temperature}°F</p>
  <p>Humidity: {status.humidity}%</p>
  <p>PH: {status.ph}</p>
  <p>Water Temperature: {status.wtemp}</p>
  <button on:click={getStatus}>Refresh</button>

  <h2>Set Ideal Ranges</h2>
  {#each Object.entries(idealRanges) as [key, value]}
    <fieldset>
      <legend>{key}</legend>
      <label>Min: <input type="number" bind:value={value.min} step="any" /></label>
      <label>Max: <input type="number" bind:value={value.max} step="any" /></label>
      <label>Target: <input type="number" bind:value={value.target} step="any" /></label>
    </fieldset>
  {/each}
  <button on:click={setRanges}>Set Ranges</button>

  <h2>Set Sensor Pins</h2>
  {#each Object.entries(pins) as [key, value]}
    <label>{key}: <input type="number" bind:value={pins[key]} min="0" max="7" /></label>
  {/each}
  <button on:click={setPins}>Set Pins</button>
</main>
