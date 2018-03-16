<h1 align="center">odinair's cogs</h1>
<p align="center">Some home-grown cogs, which may or may not be useful.</p>
<p align="center">
  <a href="https://python.org/"><img src="https://img.shields.io/badge/Python-3.5-red.svg"></a>
</p>

# Installation

This branch is not officially supported anymore, and as such may not receive updates as often.

I am, however, working on porting these cogs to Red V3 on a [separate branch](https://github.com/notodinair/Red-Cogs/tree/v3);
please feel free to try them out and report any issues you may find!

```
[p]cog repo add odinair https://github.com/notodinair/Red-Cogs.git
[p]cog install odinair <cog>
[p]load <cog>
```

# Contact

If you've either found a bug or would like to make a suggestion, please [open an issue](https://github.com/notodinair/Red-Cogs/issues/new),
as this is by far the best way to make sure that I notice it.

Otherwise, you can contact me on Discord (`odinair#0001`) or Twitter (`@odinair_`).

# Cogs

Any references to `[p]` should be replaced with your bots command prefix.

<details>
<summary>Permission Breakdown</summary>

Break down a member's permissions based on roles and channel overwrites

#### To install

```
[p]cog install odinair permissionbreakdown
[p]load permissionbreakdown
```
</details>

<details>
<summary>Quotes</summary>

Save and retrieve quotes.

#### To install

```
[p]cog install odinair quotes
[p]load quotes
```
</details>

<details>
<summary>Starboard</summary>

Send messages to a per-guild starboard channel, all from star reactions.

- This cog requires a MongoDB server running on the host machine
- Data migration from Red v2 to Red v3 will not be officially supported due to the above requirement

#### To install

```
[p]cog install odinair starboard
[p]load starboard
```
</details>

<details>
<summary>User Profiles</summary>

Pretend it's almost like Facebook, but in Discord.

Also acts similarly to another `[p]userinfo` variation.

#### To install

```
[p]cog install odinair userprofiles
[p]load userprofiles
```
</details>

<details>
<summary>Warnings</summary>

Warn users, optionally also performing a kick or ban at specified warning count thresholds.

#### To install

```
[p]cog install odinair warnings
[p]load warnings
```
</details>
