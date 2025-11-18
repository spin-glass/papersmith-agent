"""エラーハンドリングユーティリティのテスト

Requirements: 3.5
"""

from unittest.mock import Mock, patch

import httpx

from ui.utils.error_handler import ErrorHandler, LoadingState, validate_input


class TestErrorHandler:
    """ErrorHandlerクラスのテスト"""

    def test_handle_503_error(self):
        """503エラー（インデックス未準備）の処理をテスト"""
        # モックレスポンスを作成
        mock_response = Mock()
        mock_response.status_code = 503
        mock_response.json.return_value = {"detail": "Index not ready"}

        error = httpx.HTTPStatusError(
            "Service Unavailable",
            request=Mock(),
            response=mock_response
        )

        # エラーハンドリングを実行（streamlitのモックが必要）
        with patch('ui.utils.error_handler.st') as mock_st:
            ErrorHandler.handle_api_error(error, "テスト処理")

            # warningが呼ばれたことを確認
            mock_st.warning.assert_called_once()
            call_args = mock_st.warning.call_args[0][0]
            assert "準備中" in call_args or "503" in str(call_args)

    def test_handle_404_error(self):
        """404エラーの処理をテスト"""
        mock_response = Mock()
        mock_response.status_code = 404

        error = httpx.HTTPStatusError(
            "Not Found",
            request=Mock(),
            response=mock_response
        )

        with patch('ui.utils.error_handler.st') as mock_st:
            ErrorHandler.handle_api_error(error, "リソース取得")

            # errorが呼ばれたことを確認
            mock_st.error.assert_called_once()
            call_args = mock_st.error.call_args[0][0]
            assert "見つかりません" in call_args or "404" in str(call_args)

    def test_handle_connect_error(self):
        """接続エラーの処理をテスト"""
        error = httpx.ConnectError("Connection refused")

        with patch('ui.utils.error_handler.st') as mock_st:
            ErrorHandler.handle_api_error(error, "API接続")

            # errorが呼ばれたことを確認
            mock_st.error.assert_called_once()
            call_args = mock_st.error.call_args[0][0]
            assert "接続" in call_args or "Connect" in str(call_args)

    def test_handle_timeout_error(self):
        """タイムアウトエラーの処理をテスト"""
        error = httpx.TimeoutException("Request timeout")

        with patch('ui.utils.error_handler.st') as mock_st:
            ErrorHandler.handle_api_error(error, "データ取得")

            # errorが呼ばれたことを確認
            mock_st.error.assert_called_once()
            call_args = mock_st.error.call_args[0][0]
            assert "タイムアウト" in call_args or "timeout" in str(call_args).lower()


class TestValidateInput:
    """validate_input関数のテスト"""

    def test_validate_empty_input(self):
        """空の入力の検証をテスト"""
        with patch('ui.utils.error_handler.st') as mock_st:
            result = validate_input("", "テストフィールド")

            assert result is False
            mock_st.warning.assert_called_once()

    def test_validate_whitespace_input(self):
        """空白のみの入力の検証をテスト"""
        with patch('ui.utils.error_handler.st') as mock_st:
            result = validate_input("   ", "テストフィールド")

            assert result is False
            mock_st.warning.assert_called_once()

    def test_validate_valid_input(self):
        """有効な入力の検証をテスト"""
        with patch('ui.utils.error_handler.st') as mock_st:
            result = validate_input("有効な入力", "テストフィールド")

            assert result is True
            mock_st.warning.assert_not_called()

    def test_validate_min_length(self):
        """最小文字数の検証をテスト"""
        with patch('ui.utils.error_handler.st') as mock_st:
            result = validate_input("a", "テストフィールド", min_length=3)

            assert result is False
            mock_st.warning.assert_called_once()
            call_args = mock_st.warning.call_args[0][0]
            assert "3文字以上" in call_args


class TestLoadingState:
    """LoadingStateクラスのテスト"""

    def test_spinner(self):
        """スピナー表示のテスト"""
        with patch('ui.utils.error_handler.st') as mock_st:
            LoadingState.spinner("テストメッセージ")

            mock_st.spinner.assert_called_once_with("テストメッセージ")

    def test_progress_bar(self):
        """プログレスバー表示のテスト"""
        with patch('ui.utils.error_handler.st') as mock_st:
            LoadingState.progress_bar(total=100, current=50, message="処理中")

            mock_st.progress.assert_called_once()
            # プログレスが0.5（50/100）であることを確認
            call_args = mock_st.progress.call_args
            assert call_args[0][0] == 0.5

    def test_progress_bar_zero_total(self):
        """総数が0の場合のプログレスバーのテスト"""
        with patch('ui.utils.error_handler.st') as mock_st:
            LoadingState.progress_bar(total=0, current=0, message="処理中")

            mock_st.progress.assert_called_once()
            # プログレスが0であることを確認
            call_args = mock_st.progress.call_args
            assert call_args[0][0] == 0
