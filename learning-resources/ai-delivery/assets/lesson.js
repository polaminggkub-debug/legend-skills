(function () {
  "use strict";

  function wireQuiz(quiz) {
    var answer = quiz.getAttribute("data-answer");
    var feedback = quiz.querySelector(".quiz-feedback");
    var buttons = quiz.querySelectorAll("[data-option]");
    buttons.forEach(function (button) {
      button.addEventListener("click", function () {
        var isCorrect = button.getAttribute("data-option") === answer;
        buttons.forEach(function (other) {
          other.classList.remove("correct", "incorrect");
          other.setAttribute("aria-pressed", "false");
        });
        button.classList.add(isCorrect ? "correct" : "incorrect");
        button.setAttribute("aria-pressed", "true");
        feedback.classList.toggle("error", !isCorrect);
        feedback.textContent = isCorrect
          ? "ถูกต้อง — " + quiz.getAttribute("data-explanation")
          : "ลองอีกครั้ง — " + quiz.getAttribute("data-hint");
      });
    });
  }

  function wireRubric(practice) {
    var toggle = practice.querySelector("[data-toggle-rubric]");
    var rubric = practice.querySelector(".rubric");
    if (!toggle || !rubric) return;
    toggle.addEventListener("click", function () {
      var visible = rubric.classList.toggle("visible");
      toggle.setAttribute("aria-expanded", String(visible));
      toggle.textContent = visible ? "ซ่อนเกณฑ์ตรวจ" : "เปิดเกณฑ์ตรวจ";
    });
  }

  function wireCompletion() {
    var key = document.body.getAttribute("data-lesson");
    var marker = document.querySelector("[data-mark-complete]");
    if (!key || !marker) return;
    var storageKey = "ai-delivery-pack-complete-" + key;
    var done = false;
    try { done = window.localStorage.getItem(storageKey) === "yes"; } catch (error) { /* Session-only fallback. */ }
    var update = function () {
      marker.textContent = done ? "ทำบทนี้แล้ว ✓" : "ทำบทนี้เสร็จ";
      marker.setAttribute("aria-pressed", String(done));
      marker.classList.toggle("correct", done);
    };
    marker.addEventListener("click", function () {
      done = !done;
      try { window.localStorage.setItem(storageKey, done ? "yes" : "no"); } catch (error) { /* Keep working without persistence. */ }
      update();
    });
    update();
  }

  document.querySelectorAll(".quiz").forEach(wireQuiz);
  document.querySelectorAll(".practice").forEach(wireRubric);
  wireCompletion();
}());
