"""
Docker log collector module.
Retrieves logs from Docker containers.
"""

import docker


def get_container_logs(container_name, tail=100):
    """
    Get recent logs from a Docker container.

    Args:
        container_name (str): Name of the container
        tail (int): Number of recent log lines to retrieve

    Returns:
        str: Container logs
    """
    client = docker.from_env()
    container = client.containers.get(container_name)
    logs = container.logs(tail=tail).decode('utf-8')
    return logs


if __name__ == "__main__":
    # Test code
    print("Docker Log Collector - Test Mode")

    # Try to list containers
    try:
        client = docker.from_env()
        containers = client.containers.list()
        print(f"\nFound {len(containers)} running containers:")
        for container in containers:
            print(f"  - {container.name}")
    except Exception as e:
        print(f"\nError connecting to Docker: {e}")
        print("Make sure Docker is running and accessible.")
```

### Step 3: Notice What VS Code Does

As you type (or after pasting), you'll see:

1. **Syntax highlighting** - Different colors for keywords, strings, comments
2. **A squiggly line under `docker`** - Hover over it:
   - It says: "Import 'docker' could not be resolved"
   - This is fine - we haven't installed the library yet

### Step 4: Save the File

**Press `Ctrl+S`**

Watch:
- The dot next to the filename in the tab disappears (means it's saved)
- The file might auto-format slightly

---

## See Git Changes Visually

Now let's see VS Code's Git integration in action!

### Step 1: Open Source Control Panel

**Click the Source Control icon** in the left sidebar (looks like a branching tree, or press `Ctrl+Shift+G`)

You should see:
```
SOURCE CONTROL
──────────────
MESSAGE
[Empty text box]

Changes (1)
  U src/collectors/docker_collector.py
```

The `U` means **Untracked** - Git hasn't seen this file before.

### Step 2: Stage the File

**Hover over the filename** and you'll see a `+` icon appear.

**Click the `+`**

The file moves:
```
Staged Changes (1)
  A src/collectors/docker_collector.py
```

The `A` means **Added** - ready to commit!

### Step 3: Write a Commit Message

**Click in the "MESSAGE" text box** at the top.

Type:
```
Add basic Docker collector module

- Create docker_collector.py with log collection function
- Add function to list running containers
- Include test mode for verification
