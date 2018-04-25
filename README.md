<h1 align="center">odinair's cogs</h1>
<p align="center">Some home-grown cogs, which may or may not be useful.</p>
<p align="center">
  <a href="https://python.org/"><img src="https://img.shields.io/badge/Python-3.5-red.svg"></a>
</p>

**These cogs are no longer maintained.** This repository is kept as an archive of sorts, to allow others to rip code from it as needed.

Though honestly, I don't know why anyone would want to touch these things with a ten foot pole,
since most of the codebase here is pretty bad, and almost nearly unmaintainable as-is.

If you're looking for Red V3 cogs however, I'm working on updating these cogs on my [Swift-Cogs](https://github.com/notodinair/Swift-Cogs) repository.

# Installation

```
[p]cog repo add odinair https://github.com/notodinair/Red-Cogs.git
[p]cog install odinair <cog>
[p]load <cog>
```

# Contact

These cogs will not be receiving any updates, not for bugfixes nor new features.

If you've found a security issue with these cogs however, please contact me on Discord (`odinair#0001`) - I can be found lurking in the Red support servers most of the time.

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
