#!/bin/bash
MAX_ITERATIONS=20
PROMPT_CONTENT=$(cat .ralph/prompt.md)

for i in $(seq 1 $MAX_ITERATIONS); do
  echo "=== Iteration $i / $MAX_ITERATIONS === $(date '+%H:%M:%S')"

  OUTPUT=$(claude --dangerously-skip-permissions --print "$PROMPT_CONTENT")

  if echo "$OUTPUT" | grep -q "<promise>COMPLETE</promise>"; then
    echo "✓ All tasks complete!"
    exit 0
  fi

  echo "→ Iteration $i done at $(date '+%H:%M:%S'). Continuing..."
done

echo "Reached max iterations"
