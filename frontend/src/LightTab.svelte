<script>
  export let currentLightOn;
  export let currentLightOff;
  export let lightOn;
  export let lightOff;
  export let to12Hour;
  export let saveLightSchedule;
</script>

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