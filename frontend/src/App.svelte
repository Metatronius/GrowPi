<script>
  let status = {};

  async function getStatus() {
    const res = await fetch('/api/status');
    status = await res.json();
  }

  getStatus();
</script>

<main>
  <h1>GrowPi Status</h1>
  <p>Temperature: {status.temperature}°F</p>
  <p>Humidity: {status.humidity}%</p>
  <button on:click={getStatus}>Refresh</button>
</main>
