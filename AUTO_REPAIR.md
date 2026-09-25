# Automatic playlist repair

The `Repair playlist links` GitHub Actions workflow checks the remote MP3 links
once a week. When a link has moved, `auto_repair.py` derives the source album
page from the existing URL, finds the song by its exact normalized title, and
updates only that song's `src` value.

The script deliberately leaves a song unchanged when the title match is
ambiguous or a replacement cannot be verified. It also stops without changing
anything if more than 35% of all links fail at once, since that usually means
the remote host blocked the checker rather than thousands of files moving.

## GitHub setup

1. Push these files to the repository's default branch.
2. Open **Settings > Actions > General** in the GitHub repository.
3. Under **Workflow permissions**, select **Read and write permissions** and
   save.
4. Open **Actions > Repair playlist links > Run workflow** for the first test.

## Local commands

Install dependencies:

```powershell
py -m pip install -r requirements-repair.txt
```

Check one playlist without saving changes:

```powershell
py auto_repair.py --dry-run --playlist playlists/NDS/marioKartDS.json
```

Check and repair every playlist:

```powershell
py auto_repair.py
```
