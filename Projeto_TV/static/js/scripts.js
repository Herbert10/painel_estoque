document.addEventListener('DOMContentLoaded', () => {
    const carousel = document.getElementById('carousel');
    const images = carousel.getElementsByTagName('img');
    let index = 0;

    function showNextImage() {
        images[index].classList.remove('active');
        index = (index + 1) % images.length;
        images[index].classList.add('active');
    }

    setInterval(showNextImage, 5000); // Troca a imagem a cada 5 segundos

    // Carregar vídeos em loop na parte direita
    const videoPlayer = document.getElementById('video-player');
    const videoFiles = ['caminho/para/video1.mp4', 'caminho/para/video2.mp4']; // Adicione os caminhos dos vídeos
    let videoIndex = 0;

    function playNextVideo() {
        videoPlayer.src = videoFiles[videoIndex];
        videoPlayer.play();
        videoIndex = (videoIndex + 1) % videoFiles.length;
    }

    videoPlayer.addEventListener('ended', playNextVideo);
    playNextVideo();
});
