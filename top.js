if (interaction.customId === "top") {

  const all = await db.all();
  const top = all
    .filter(d => d.id.startsWith("points_"))
    .sort((a, b) => b.value - a.value)
    .slice(0, 10);

  let desc = "";
  for (let i = 0; i < top.length; i++) {
    desc += `🥇 **${i + 1}.** <@${top[i].id.replace("points_","")}> — **${top[i].value}**\n`;
  }

  const embed = new EmbedBuilder()
    .setColor("#FFD700") // ذهبي
    .setTitle("🏆 Top Points")
    .setDescription(desc || "لا يوجد بيانات");

  interaction.reply({ embeds: [embed] });
}
