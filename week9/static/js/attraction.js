window.addEventListener("DOMContentLoaded", async () => {
  const placeId = window.location.pathname.split("/")[2];
  const attraction_id = `/api/attraction/${placeId}`;
  try {
    const response = await fetch(attraction_id);
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

      // input 日曆的樣式
      document
        .querySelector(".calendar")
        .setAttribute("placeholder", "yyyy/mm/dd");

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
});
