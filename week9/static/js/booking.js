window.addEventListener("DOMContentLoaded", async () => {
  const token = localStorage.getItem("token");

  if (!token) {
    window.location.href = "/";
    return;
  }
});
window.addEventListener("DOMContentLoaded", async () => {
  try {
    const token = localStorage.getItem("token");

    let userName = "";
    const payload = jwt_decode(token);
    userName = payload.data.name;

    console.log("準備發送 fetch");
    const response = await fetch("/api/booking", {
      method: "GET",
      headers: {
        "Content-Type": "application/json",
        Authorization: "Bearer " + token,
      },
    });
    console.log("fetch 完成，response：", response);
    console.log("Status code:", response.status); // 這裡會印出 200、400、401、500 之類的

    const data = await response.json();
    console.log(data);

    if (data.data) {
      let textContent = "";
      if (data.data.time === "上半天") {
        textContent = "早上 9 點到下午 4 點";
      } else {
        textContent = "下午 2 點到晚上 9 點";
      }

      console.log("圖片網址：", data.data.attraction.images);
      document.querySelector(".img").src = data.data.attraction.images;
      document.querySelector(".name").textContent = data.data.attraction.name;
      document.querySelector(".date").textContent = data.data.date;
      document.querySelector(".time").textContent = textContent;
      document.querySelector(
        ".price"
      ).textContent = `新台幣 ${data.data.price} 元`;
      document.querySelector(".address").textContent =
        data.data.attraction.address;
      document.querySelector(".headline-2").textContent = userName;
      document.querySelector(
        "span.total"
      ).textContent = `新台幣 ${data.data.price} 元`;
    } else {
      console.log("目前沒有預定行程");
      document.querySelector(".headline-2").textContent = userName;

      document.querySelector("main.none").innerHTML = `
      <p class="none">目前沒有任何待預訂的行程</p>`;
    }

    document.querySelector(".delete").addEventListener("click", async () => {
      const token = localStorage.getItem("token"); // 確保有 token

      const response = await fetch("/api/booking", {
        method: "DELETE",
        headers: {
          "Content-Type": "application/json",
          Authorization: "Bearer " + token,
        },
      });
      if (response.ok) {
        location.reload();
        console.log("刪除成功！");
      } else {
        console.log("刪除失敗！");
      }
    });
  } catch (error) {
    console.error("Fetch 發生錯誤：", error);
  }
});

