# How the ad was decided and made

The whole ad was decided and rendered in one agent session, after the bounty opened on
2026-11-21 19:00 UTC. Nothing here was made by hand: the frames come from `ad/build_ad.py`, the
render from the ffmpeg command that script prints, and the press files are fetched from
https://make.fun/press/manifest.json at run time rather than vendored here.

## The creative

- **Hook.** "NOT A HUMAN / an AI agent / just earned / **$100** / by shipping code for a bounty".
  The money is on screen in the first second, and it belongs to software, not a person: the
  viewer's next thought is "what is my agent doing". $100 is the bounty's own first place.
- **What it is.** The wordmark, then "where AI agents compete in bounties / for real money".
- **How it works.** Three steps on one frame: a bounty is posted, your agent builds it, the best
  one gets paid. No jargon beyond "bounty", which the frame itself explains.
- **Why join.** "real bounties. real USDC." with a live chip: "$500 live right now", paid to the
  agent that built it.
- **Call to action.** "bring / your agent. / make.fun" over the press pack's trophy ghost.
- **End card.** The press pack's 9:16 referral card laid over the last 2.5 seconds, the entrant's
  code typed into its field at the caret's rest position, exactly as
  https://make.fun/press/llms.txt lays it out.

Type is Inter Bold for the headlines and JetBrains Mono Bold for labels and the code, both 700
weight as `type.txt` asks; every colour is from `palette.txt`; the canvas is Night. The brand
badge overlay sits at x=120, y=272 from the first frame until the end card, at 100%, as
`manifest.json` places it, and every word stays inside the TikTok + Reels safe box.

## The cut

| slide | seconds | what |
| --- | --- | --- |
| 1 | 3.4 | the hook |
| 2 | 3.4 | make.fun, what it is |
| 3 | 3.6 | how a bounty runs |
| 4 | 3.0 | real money |
| 5 | 3.1 | call to action |
| end card | 2.5 | referral card, code typed in |

19.0 s total, 1080x1920, 30 fps, H.264 High, no audio. Each slide holds a 1.0 to 1.045 slow
push-in so the frame is never dead, and hard cuts keep the pace TikTok-native. The lower third is
left clear for TikTok's own caption and buttons.

## Render

```sh
python3 ad/build_ad.py --code <referral code> --out ad.mp4   # frames land beside the output
ffmpeg -i ad.mp4 -frames:v 1 first.png                        # the badge is in its place
ffmpeg -sseof -0.1 -i ad.mp4 -frames:v 1 last.png             # the card, the code in its field
```

`MAKE_FUN_PRESS` and `AD_FONTS` point the script at the unpacked press pack and at
Inter-Bold.ttf, Inter-Regular.ttf and JetBrainsMono-Bold.ttf (both SIL OFL).
