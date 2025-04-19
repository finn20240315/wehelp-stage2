window.addEventListener("DOMContentLoaded", async () => {
  const placeId = window.location.pathname.split("/")[2];
  const attraction_url = `/api/attraction/${placeId}`;
  try {
    const response = await fetch(attraction_url);
    console.log("抓到的資料：", response);

    if (!response.ok) {
      // 不等於 response.ok
      throw new Error(`http 錯誤!狀態碼：${response.status}`);
    }
    // 讀取response
    const data = await response.json();
    // 讀取失敗
    if (!data || !data.data) {
      throw new Error("讀取失敗：API 回傳的資料為空");
    } else {
      // 讀取成功
      console.log("讀取資料成功：", data);

      // 動態生成景點資訊
      const profile = document.querySelector(".profile");
      const bookingForm = document.querySelector(".booking-form");
      const infors = document.querySelector(".infors");
      const addressTitle = document.querySelector(".address-title");
      const transportTitle = document.querySelector(".transport-title");

      const name = document.createElement("div");
      name.textContent = data.data.name;
      name.className = "name";

      const category = document.createElement("div");
      category.textContent = data.data.category;
      category.className = "category";

      const description = document.createElement("div");
      description.textContent = data.data.description;
      description.className = "description";

      const address = document.createElement("div");
      address.textContent = data.data.address;
      address.className = "address";

      const transport = document.createElement("div");
      transport.textContent = data.data.transport;
      transport.className = "transport";

      profile.insertBefore(name, bookingForm);
      profile.insertBefore(category, bookingForm);
      infors.insertBefore(description, addressTitle);
      addressTitle.appendChild(address);
      transportTitle.appendChild(transport);

      // radio 的樣式
      const radios = document.querySelectorAll(".radio");
      const priceElement = document.querySelector(".t6");

      radios.forEach((radio) => {
        radio.addEventListener("change", function () {
          const selectedPrice = this.value;
          priceElement.textContent = `新台幣 ${selectedPrice} 元`;
        });
      });

      // 取得圖片容器
      const imgContainer = document.querySelector(".img-container");
      const progressBar = document.querySelector(".progress-bar");

      // 清空舊內容（避免多次載入）
      imgContainer.innerHTML = "";
      progressBar.innerHTML = "";

      // 取得圖片資料
      const images = data.data.images;
      let index = 0;

      // 設置第一張圖片
      imgContainer.style.backgroundImage = `url(${images[index]})`;

      // 動態生成圓形指示器
      images.forEach((_, i) => {
        const dot = document.createElement("div");
        dot.className = "dot";
        if (i === index) {
          dot.classList.add("active");
        }

        dot.dataset.index = i;
        dot.addEventListener("click", () => {
          index = i;
          updateImage();
        });
        progressBar.appendChild(dot);
      });

      // 輪播切換
      const leftBtn = document.querySelector(".left-arrow");
      const rightBtn = document.querySelector(".right-arrow");
      console.log("左右箭頭:", leftBtn, rightBtn); // 確保選取成功

      function updateImage() {
        console.log("更新圖片，當前 index:", index); // 確保有執行
        imgContainer.style.backgroundImage = `url(${images[index]})`;
        updateDots();
      }
      function updateDots() {
        document.querySelectorAll(".dot").forEach((dot, i) => {
          dot.classList.toggle("active", i === index);
        });
      }

      rightBtn.addEventListener("click", () => {
        console.log("右箭頭被點擊"); // 檢查是否觸發
        index = (index + 1) % images.length;
        console.log("新的 index:", index); // 檢查 index 是否變更
        updateImage();
      });

      leftBtn.addEventListener("click", () => {
        console.log("左箭頭被點擊"); // 檢查是否觸發
        index = (index - 1 + images.length) % images.length;
        console.log("新的 index:", index); // 檢查 index 是否變更
        updateImage();
      });
    }
  } catch (error) {
    console.error("載入資料失敗", error);
  }

  // week13
  // 預訂行程按鈕
  const bookingBtn = document.querySelector(".booking");
  const dateInput = document.querySelector(".calendar");

  bookingBtn.addEventListener("click", async (event) => {
    console.log("📌 booking 按鈕被點擊了！");
    if (!dateInput.reportValidity()) {
      return; // 如果驗證不通過，就不要繼續往下執行
    }

    const token = localStorage.getItem("token");
    console.log("token:", token); // 確認 token 是否存在

    if (!token) {
      signUpFormContainer.style.display = "block";
      popUpArea.style.display = "block";
      return;
    }

    const attraction_id = placeId;
    const date = document.querySelector(".calendar").value;
    // if (!date) {
    //   alert("請選擇日期");
    //   return;
    // }

    const time = document
      .querySelector(".radio:checked")
      .parentElement.textContent.trim();
    const price = document.querySelector(".radio:checked").value;

    // 跳轉頁面到 "/booking"
    // 將表單資料都傳到 api : "/api/booking"
    await fetch("/api/booking", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        Authorization: "Bearer " + token,
      },
      body: JSON.stringify({
        attraction_id: attraction_id,
        date: date,
        time: time,
        price: price,
      }),
    });

    window.location.href = "/booking"; // 跳轉到預訂行程頁面
  });

  document.querySelector(".appointment").addEventListener("click", () => {
    console.log("點擊到按鈕了！");
    const token = localStorage.getItem("token");
    if (!token) {
      signUpFormContainer.style.display = "block";
      popUpArea.style.display = "block";
    } else {
      window.location.href = "/booking";
    }
  });
});
