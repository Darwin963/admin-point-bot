if (interaction.customId === "mypoints") {
  const points = await db.get(`points_${interaction.user.id}`) || 0;

  const embed = new EmbedBuilder()
    .setColor("#00ffcc")
    .setTitle("📊 نقاطك")
    .setDescription(`نقاطك الحالية: **${points}**`)
    .setFooter({ text: interaction.user.username });

  interaction.reply({ embeds: [embed], ephemeral: true });
}
