async function kiemTra() {
  const goc = document.getElementById("goc").files[0];
  const cheban = document.getElementById("cheban").files[0];

  if (!goc || !cheban) {
    alert("Vui lòng chọn đủ 2 ảnh");
    return;
  }

  const formData = new FormData();
  formData.append("goc", goc);
  formData.append("cheban", cheban);

  document.getElementById("result").innerText = "⏳ Đang xử lý...";

  const res = await fetch("/api/compare", {
    method: "POST",
    body: formData
  });

  const data = await res.json();

  if (!data.changed) {
    document.getElementById("result").innerText = "✅ Không có thay đổi";
    document.getElementById("highlight").src = "";
  } else {
    document.getElementById("result").innerText =
      `⚠️ Có thay đổi, ${data.regions} vùng khác biệt`;
    document.getElementById("highlight").src = data.image_url;
  }
}
