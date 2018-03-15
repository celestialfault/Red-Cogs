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

**To install:**

- `[p]cog install odinair permissionbreakdown`
- `[p]load permissionbreakdown`

**Basic usage:**

- `[p]permissionbreakdown [user] [channel] [page=1]` - break down `user`s permissions, optionally also factoring in `channel`s overwrites for `user`
- `[p]permissionbreakdown role <role> [channel]` - break down the permissions for `role`, optionally factoring in `channel`s overwrites
</details>

<details>
<summary>Quotes</summary>

Save and retrieve quotes.

**To install:**

- `[p]cog install odinair quotes`
- `[p]load quotes`

**Basic usage:**

- `[p]quote [quote]` - retrieve either `quote` or a random quote
- `[p]quote add This is a quote!` - add a quote with text `This is a quote!`
- `[p]quote list` - sends a list of the guilds quotes in a direct message
- `[p]quote remove <quote>` - delete `quote`
</details>

<details>
<summary>Starboard</summary>

Send messages to a per-guild starboard channel, all from star reactions.

- This cog requires a MongoDB server running on the host machine
- Data migration from Red v2 to Red v3 will not be officially supported due to the above requirement

**To install:**

- `[p]cog install odinair starboard`
- `[p]load starboard`

**Basic usage:**

- `[p]star <message id>` - star or unstar a message by its id; this is an alternative to adding or removing a star reaction to the message
- `[p]starboard blacklist` - manage the guilds starboard blacklist
- `[p]starboard channel <channel>` - set the guilds starboard channel
- `[p]starboard minstars <amount>` - set the minimum amount of stars a message must receive to be sent to the starboard
- `[p]starboard remove <message id>` - removes a message from the starboard
- `[p]starboard selfstar` - toggles if members can star their own messages
- `[p]starboard stats [member]` - returns some basic statistics on yourself or the specified members
</details>

<details>
<summary>User Profiles</summary>

Pretend it's almost like Facebook, but in Discord.

Also acts similarly to another `[p]userinfo` variation.

**To install:**

- `[p]cog install odinair userprofiles`
- `[p]load userprofiles`

**Basic usage:**

- `[p]user [member]` - get your or the specified member's user profile
- `[p]help user`
</details>

<details>
<summary>Warnings</summary>

Warn users, optionally also performing a kick or ban at specified warning count thresholds.

**To install:**

- `[p]cog install odinair warnings`
- `[p]load warnings`

**Basic usage:**

- `[p]warn <member> <reason>` - warns `member` for `reason`
- `[p]warn clear <member>` - clears all recorded warnings for `member`
- `[p]warn list [member] [page=1]` - list recorded warnings for `member`
- `[p]warn remove <member> <warning>` - removes a recorded warning with the specified id from `member`
- `[p]warnset ban [warnings=0]` - set the amount of warnings required to automatically ban; set this to 0 to disable
- `[p]warnset delete [days=0]` - set how many days worth of messages should be deleted upon autobanning
- `[p]warnset kick [warnings=0]` - set the amount of warnings required to automatically kick; set this to 0 to disable
</details>
