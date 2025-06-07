<script>
  export let emailSettings;
  export let saveEmailSettings;
</script>

<h2>Email Settings</h2>
<form on:submit|preventDefault={saveEmailSettings}>
  <label>
    SMTP Server:
    <input type="text" bind:value={emailSettings.smtp_server} />
  </label>
  <label>
    SMTP Port:
    <input type="number" bind:value={emailSettings.smtp_port} />
  </label>
  <label>
    Username:
    <input type="text" bind:value={emailSettings.username} />
  </label>
  <label>
    Password:
    <input type="password" bind:value={emailSettings.password} />
  </label>
  <label>
    From Email:
    <input type="email" bind:value={emailSettings.from_email} />
  </label>
  <label>
    To Email:
    <input type="email" bind:value={emailSettings.to_email} />
  </label>
  <button type="submit">Save Email Settings</button>
</form>